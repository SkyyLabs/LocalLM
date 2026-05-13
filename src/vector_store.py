from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from src.indexing import IndexedChunk
from src.metadata import Metadata, metadata_matches_filters


@dataclass(frozen=True)
class SearchResult:
    id: str
    text: str
    metadata: dict[str, Any]
    score: float


class VectorStore(Protocol):
    def add(self, chunks: list[IndexedChunk]) -> None:
        ...

    def search(self, query_embedding: list[float], limit: int, filters: Metadata | None = None) -> list[SearchResult]:
        ...


class ChromaVectorStore:
    def __init__(self, index_dir: Path, collection_name: str = "private_documents") -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("Chroma is not installed. Run: pip install chromadb") from exc

        self.client = chromadb.PersistentClient(path=str(index_dir / "chroma"))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add(self, chunks: list[IndexedChunk]) -> None:
        if not chunks:
            return
        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=[chunk.embedding for chunk in chunks],
            metadatas=[_chroma_metadata(chunk.metadata) for chunk in chunks],
        )

    def search(self, query_embedding: list[float], limit: int, filters: Metadata | None = None) -> list[SearchResult]:
        where = _chroma_metadata(filters or {}) or None
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            SearchResult(
                id=str(item_id),
                text=str(document),
                metadata=dict(metadata or {}),
                score=float(distance),
            )
            for item_id, document, metadata, distance in zip(ids, documents, metadatas, distances, strict=False)
        ]


class FaissVectorStore:
    def __init__(self, index_dir: Path) -> None:
        try:
            import faiss
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("FAISS is not installed. Run: pip install '.[faiss]'") from exc

        self.faiss = faiss
        self.np = np
        self.index_dir = index_dir / "faiss"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "index.faiss"
        self.records_path = self.index_dir / "records.json"
        self.records: list[dict[str, Any]] = self._load_records()
        self.index = self._load_index()

    def add(self, chunks: list[IndexedChunk]) -> None:
        if not chunks:
            return
        vectors = self.np.array([chunk.embedding for chunk in chunks], dtype="float32")
        self._normalize(vectors)
        if self.index is None:
            self.index = self.faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.records.extend(
            {"id": chunk.id, "text": chunk.text, "metadata": chunk.metadata} for chunk in chunks
        )
        self.faiss.write_index(self.index, str(self.index_path))
        self.records_path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

    def search(self, query_embedding: list[float], limit: int, filters: Metadata | None = None) -> list[SearchResult]:
        if self.index is None or not self.records:
            return []
        vector = self.np.array([query_embedding], dtype="float32")
        self._normalize(vector)
        distances, indexes = self.index.search(vector, min(max(limit * 5, limit), len(self.records)))
        results: list[SearchResult] = []
        for distance, index in zip(distances[0], indexes[0], strict=False):
            if index < 0:
                continue
            record = self.records[int(index)]
            if filters and not metadata_matches_filters(record.get("metadata", {}), filters):
                continue
            results.append(
                SearchResult(
                    id=str(record["id"]),
                    text=str(record["text"]),
                    metadata=dict(record.get("metadata", {})),
                    score=float(distance),
                )
            )
            if len(results) >= limit:
                break
        return results

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.records_path.exists():
            return []
        data = json.loads(self.records_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise RuntimeError("FAISS records file is invalid.")
        return data

    def _load_index(self) -> Any:
        if not self.index_path.exists():
            return None
        return self.faiss.read_index(str(self.index_path))

    def _normalize(self, vectors: Any) -> None:
        norms = self.np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vectors /= norms


class JsonVectorStore:
    """Small dependency-free fallback for tests and tiny local collections."""

    def __init__(self, index_dir: Path) -> None:
        self.index_dir = index_dir / "json"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.records_path = self.index_dir / "records.json"
        self.records: list[dict[str, Any]] = self._load_records()

    def add(self, chunks: list[IndexedChunk]) -> None:
        known_ids = {record["id"] for record in self.records}
        self.records = [record for record in self.records if record["id"] not in {chunk.id for chunk in chunks}]
        known_ids -= {chunk.id for chunk in chunks}
        self.records.extend(
            {
                "id": chunk.id,
                "text": chunk.text,
                "embedding": chunk.embedding,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
            if chunk.id not in known_ids
        )
        self.records_path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

    def search(self, query_embedding: list[float], limit: int, filters: Metadata | None = None) -> list[SearchResult]:
        scored: list[SearchResult] = []
        for record in self.records:
            if filters and not metadata_matches_filters(record.get("metadata", {}), filters):
                continue
            scored.append(
                SearchResult(
                    id=str(record["id"]),
                    text=str(record["text"]),
                    metadata=dict(record.get("metadata", {})),
                    score=_cosine_similarity(query_embedding, [float(value) for value in record["embedding"]]),
                )
            )
        return sorted(scored, key=lambda result: result.score, reverse=True)[:limit]

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.records_path.exists():
            return []
        data = json.loads(self.records_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise RuntimeError("JSON vector records file is invalid.")
        return data


def create_vector_store(kind: str, index_dir: Path) -> VectorStore:
    index_dir.mkdir(parents=True, exist_ok=True)
    if kind == "chroma":
        return ChromaVectorStore(index_dir)
    if kind == "faiss":
        return FaissVectorStore(index_dir)
    if kind == "auto":
        try:
            return ChromaVectorStore(index_dir)
        except RuntimeError:
            return FaissVectorStore(index_dir)
    if kind == "json":
        return JsonVectorStore(index_dir)
    raise ValueError("VECTOR_STORE must be 'auto', 'chroma', or 'faiss'.")


def _chroma_metadata(metadata: Metadata) -> Metadata:
    # Chroma accepts scalar metadata only. Tags are stored as comma-separated text.
    return {key: value for key, value in metadata.items() if isinstance(value, str | int | float | bool)}


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
