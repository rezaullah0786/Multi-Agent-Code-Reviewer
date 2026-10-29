import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.retrieval.qdrant_store import qdrant_store

# Directories and file patterns to ignore for security and cleanliness
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
}

EXCLUDED_FILES = {
    ".env",
    ".env.example",
    ".env.local",
    "id_rsa",
    "id_dsa",
    "secrets.json",
}

SUPPORTED_EXTENSIONS = {".py"}


class CodeIndexer:
    """Safely traverses local directories, chunks Python files, and indexes them into Qdrant."""

    def __init__(self, chunk_lines: int = 40, chunk_overlap: int = 10):
        self.chunk_lines = chunk_lines
        self.chunk_overlap = chunk_overlap

    def chunk_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        lines = content.splitlines()
        if not lines:
            return []

        chunks: List[Dict[str, Any]] = []
        step = max(1, self.chunk_lines - self.chunk_overlap)

        for i in range(0, len(lines), step):
            window = lines[i : i + self.chunk_lines]
            start_line = i + 1
            end_line = i + len(window)
            chunk_text = "\n".join(window).strip()
            if chunk_text:
                chunks.append(
                    {
                        "file_path": file_path,
                        "start_line": start_line,
                        "end_line": end_line,
                        "content": chunk_text,
                        "language": "python",
                    }
                )

        return chunks

    def is_safe_path(self, target_dir: str) -> Tuple[bool, str]:
        """Validates that directory path is legitimate and avoids root or sensitive system directories."""
        try:
            resolved = Path(target_dir).resolve()
            if not resolved.exists():
                return False, f"Directory does not exist: {target_dir}"
            if not resolved.is_dir():
                return False, f"Path is not a directory: {target_dir}"

            # Prevent indexing root or system directories
            str_path = str(resolved).lower()
            if str_path in ("c:\\", "c:\\windows", "c:\\windows\\system32", "/", "/etc", "/var", "/root"):
                return False, "Indexing system root directories is prohibited for security."

            return True, str(resolved)
        except Exception as e:
            return False, f"Invalid directory path: {str(e)}"

    def index_directory(
        self, directory_path: str, max_files: int = 200, recursive: bool = True
    ) -> Dict[str, Any]:
        is_safe, resolved_dir = self.is_safe_path(directory_path)
        if not is_safe:
            raise ValueError(resolved_dir)

        all_chunks: List[Dict[str, Any]] = []
        indexed_files = 0

        for root, dirs, files in os.walk(resolved_dir):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]

            for file in files:
                if indexed_files >= max_files:
                    break

                if file in EXCLUDED_FILES or file.startswith("."):
                    continue

                ext = os.path.splitext(file)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, resolved_dir)

                try:
                    # Enforce file size limit (max 500KB per file)
                    if os.path.getsize(full_path) > 500_000:
                        continue

                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        code_content = f.read()

                    file_chunks = self.chunk_file(rel_path, code_content)
                    all_chunks.extend(file_chunks)
                    indexed_files += 1
                except Exception:
                    continue

            if not recursive or indexed_files >= max_files:
                break

        chunks_stored = qdrant_store.upsert_chunks(all_chunks)

        return {
            "indexed_files": indexed_files,
            "total_chunks": chunks_stored,
            "directory": resolved_dir,
            "storage_mode": qdrant_store.storage_mode,
            "message": f"Successfully indexed {indexed_files} files into {chunks_stored} code chunks.",
        }


code_indexer = CodeIndexer()
