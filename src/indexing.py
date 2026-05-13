from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.chunking import chunk_text
from src.document_loader import SUPPORTED_EXTENSIONS, load_document
from src.embeddings import LocalOllamaEmbeddingProvider
from src.metadata import Metadata, merge_metadata


@dataclass(frozen=True)
class IndexedChunk:
    id: str
    text: str
    embedding: list[float]
    metadata: Metadata


def iter_supported_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in SUPPORTED_EXTENSIONS else []
    if not root.exists():
        raise FileNotFoundError(f"Index path not found: {root}")
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def build_index_chunks(
    *,
    path: Path,
    embedder: LocalOllamaEmbeddingProvider,
    tags: list[str] | None = None,
    cli_metadata: Metadata | None = None,
    metadata_by_file: dict[str, Metadata] | None = None,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[IndexedChunk]:
    records: list[IndexedChunk] = []
    cli_metadata = cli_metadata or {}
    metadata_by_file = metadata_by_file or {}

    for file_path in iter_supported_files(path):
        text = load_document(file_path)
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        base_metadata = merge_metadata(
            file_path=file_path,
            tags=tags,
            cli_metadata=cli_metadata,
            metadata_by_file=metadata_by_file,
        )
        for index, chunk in enumerate(chunks):
            metadata = dict(base_metadata)
            metadata["chunk_index"] = index
            records.append(
                IndexedChunk(
                    id=f"{file_path.resolve()}::{index}",
                    text=chunk,
                    embedding=embedder.embed(chunk),
                    metadata=metadata,
                )
            )
    return records
