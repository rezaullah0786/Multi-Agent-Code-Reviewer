import logging
from typing import Any, Dict, List, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings
from app.retrieval.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.schemas.index import CodeChunkResult

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """
    Manages vector storage and semantic similarity search using Qdrant.
    Supports both remote Qdrant servers and embedded local in-memory Qdrant instances.
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.dimension = self.embedding_provider.get_dimension()
        self.client: Optional[QdrantClient] = None
        self.storage_mode = "Uninitialized"
        self.is_connected = False
        self._init_client()

    def _init_client(self) -> None:
        """Initializes Qdrant client based on QDRANT_MODE (embedded, server, or auto)."""
        mode = getattr(settings, "QDRANT_MODE", "embedded").lower()

        # If explicit server mode or remote URL provided
        if mode == "server" or (mode == "auto" and settings.QDRANT_URL):
            try:
                if settings.QDRANT_URL:
                    remote_client = QdrantClient(
                        url=settings.QDRANT_URL,
                        api_key=settings.QDRANT_API_KEY,
                        prefer_grpc=False,
                        timeout=1.0,
                    )
                else:
                    remote_client = QdrantClient(
                        host=settings.QDRANT_HOST,
                        port=settings.QDRANT_PORT,
                        prefer_grpc=False,
                        timeout=1.0,
                    )
                remote_client.get_collections()
                self.client = remote_client
                self.storage_mode = f"Qdrant Server ({settings.QDRANT_HOST}:{settings.QDRANT_PORT})"
                self.is_connected = True
                self._ensure_collection()
                logger.info(f"Connected to remote Qdrant server at {self.storage_mode}")
                return
            except Exception as err:
                logger.warning(f"Remote Qdrant server connection failed ({err}). Falling back to embedded mode.")

        # Default: Real embedded Qdrant (in-memory)
        try:
            self.client = QdrantClient(":memory:")
            self.storage_mode = "Qdrant Embedded (In-Memory)"
            self.is_connected = True
            self._ensure_collection()
            logger.info("Initialized real Qdrant embedded in-memory instance.")
        except Exception as emb_err:
            logger.error(f"Failed to initialize embedded Qdrant: {emb_err}")
            self.storage_mode = "Unavailable"
            self.is_connected = False

    def _ensure_collection(self) -> None:
        if not self.client:
            return
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimension,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")

    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        if not self.client or not self.is_connected or not chunks:
            return 0

        texts = [c["content"] for c in chunks]
        vectors = self.embedding_provider.embed_texts(texts)

        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            point_id = str(uuid.uuid4())
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "chunk_id": point_id,
                        "file_path": chunk.get("file_path", "unknown"),
                        "start_line": chunk.get("start_line", 1),
                        "end_line": chunk.get("end_line", 1),
                        "content": chunk.get("content", ""),
                        "language": chunk.get("language", "python"),
                    },
                )
            )

        try:
            self.client.upsert(collection_name=self.collection_name, points=points)
            return len(points)
        except Exception as e:
            logger.error(f"Failed to upsert points into Qdrant: {e}")
            return 0

    def search(
        self, query: str, limit: int = 5, file_filter: Optional[str] = None
    ) -> List[CodeChunkResult]:
        if not self.client or not self.is_connected or not query.strip():
            return []

        query_vec = self.embedding_provider.embed_query(query)

        try:
            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vec,
                    limit=limit,
                )
                scored_points = response.points
            else:
                scored_points = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vec,
                    limit=limit,
                )

            results: List[CodeChunkResult] = []
            for sp in scored_points:
                payload = sp.payload or {}
                f_path = payload.get("file_path", "")
                if file_filter and file_filter.lower() not in f_path.lower():
                    continue

                results.append(
                    CodeChunkResult(
                        chunk_id=str(sp.id),
                        file_path=f_path,
                        start_line=int(payload.get("start_line", 1)),
                        end_line=int(payload.get("end_line", 1)),
                        content=str(payload.get("content", "")),
                        score=float(sp.score),
                        language=str(payload.get("language", "python")),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to query Qdrant: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        count = 0
        if self.client and self.is_connected:
            try:
                info = self.client.get_collection(self.collection_name)
                count = info.points_count or 0
            except Exception:
                count = 0

        return {
            "is_connected": self.is_connected,
            "storage_mode": self.storage_mode,
            "collection_name": self.collection_name,
            "total_chunks": count,
            "dimension": self.dimension,
            "embedding_provider": self.embedding_provider.__class__.__name__,
        }


qdrant_store = QdrantVectorStore()
