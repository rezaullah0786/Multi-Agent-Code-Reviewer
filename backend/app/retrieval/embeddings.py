from abc import ABC, abstractmethod
import hashlib
import math
import re
from typing import List, Optional
import httpx

from app.config import settings


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        pass


class LocalHashingEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic local vectorizer that maps text into a normalized 384-dimensional space
    using token n-gram hashing and frequency projection.
    Provides offline demonstration vector search without external API dependencies.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _vectorize(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return vec

        for i, token in enumerate(tokens):
            # Unigram hash
            h1 = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.dimension
            vec[h1] += 1.0

            # Bigram hash for sequence awareness
            if i + 1 < len(tokens):
                bigram = f"{token}_{tokens[i + 1]}"
                h2 = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16) % self.dimension
                vec[h2] += 1.5

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [x / norm for x in vec]
        return vec

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._vectorize(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._vectorize(query)

    def get_dimension(self) -> int:
        return self.dimension


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI Embedding Provider using text-embedding-3-small or configured model."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIM
        self.fallback = LocalHashingEmbeddingProvider(self.dimension)

    def is_available(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your-"))

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.is_available() or not texts:
            return self.fallback.embed_texts(texts)

        try:
            with httpx.Client(timeout=settings.LLM_REQUEST_TIMEOUT) as client:
                res = client.post(
                    f"{self.base_url.rstrip('/')}/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"input": texts, "model": self.model},
                )
                res.raise_for_status()
                data = res.json()
                return [item["embedding"] for item in data["data"]]
        except Exception:
            # Graceful fallback to deterministic local embedding
            return self.fallback.embed_texts(texts)

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * self.dimension

    def get_dimension(self) -> int:
        return self.dimension


def get_embedding_provider() -> BaseEmbeddingProvider:
    if settings.EMBEDDING_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return OpenAIEmbeddingProvider()
    return LocalHashingEmbeddingProvider(settings.EMBEDDING_DIM)
