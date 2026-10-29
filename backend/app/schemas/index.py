from typing import List, Optional
from pydantic import BaseModel, Field


class IndexDirectoryRequest(BaseModel):
    directory_path: str = Field(..., description="Local directory path to index for semantic code search")
    recursive: bool = Field(default=True, description="Scan subdirectories recursively")
    max_files: int = Field(default=200, ge=1, le=1000, description="Max files to index per request")


class IndexStatusResponse(BaseModel):
    status: str
    indexed_files: int
    total_chunks: int
    collection_name: str
    storage_mode: str
    directory: str
    message: str


class CodeSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Search query or code snippet")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum chunks to return")
    file_filter: Optional[str] = Field(default=None, description="Optional substring to filter by file path")


class CodeChunkResult(BaseModel):
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    score: float
    language: str = "python"


class CodeSearchResponse(BaseModel):
    query: str
    results: List[CodeChunkResult]
    total_results: int
    storage_mode: str
