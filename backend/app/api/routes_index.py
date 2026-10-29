from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from app.retrieval.code_indexer import code_indexer
from app.retrieval.qdrant_store import qdrant_store
from app.schemas.index import (
    CodeSearchRequest,
    CodeSearchResponse,
    IndexDirectoryRequest,
    IndexStatusResponse,
)

router = APIRouter(tags=["Repository Indexing & Search"])


@router.post("/index", response_model=IndexStatusResponse)
def index_local_directory(request: IndexDirectoryRequest) -> IndexStatusResponse:
    """Indexes source code files in a validated local directory into Qdrant."""
    try:
        result = code_indexer.index_directory(
            directory_path=request.directory_path,
            max_files=request.max_files,
            recursive=request.recursive,
        )
        return IndexStatusResponse(
            status="completed",
            indexed_files=result["indexed_files"],
            total_chunks=result["total_chunks"],
            collection_name=qdrant_store.collection_name,
            storage_mode=result["storage_mode"],
            directory=result["directory"],
            message=result["message"],
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        )


@router.get("/index/status", response_model=Dict[str, Any])
def get_index_status() -> Dict[str, Any]:
    """Retrieves current Qdrant vector index status and chunk counts."""
    return qdrant_store.get_status()


@router.post("/search", response_model=CodeSearchResponse)
def search_codebase(request: CodeSearchRequest) -> CodeSearchResponse:
    """Performs semantic vector search across indexed codebase chunks."""
    results = qdrant_store.search(
        query=request.query,
        limit=request.limit,
        file_filter=request.file_filter,
    )
    return CodeSearchResponse(
        query=request.query,
        results=results,
        total_results=len(results),
        storage_mode=qdrant_store.storage_mode,
    )
