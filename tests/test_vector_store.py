from __future__ import annotations

from pathlib import Path

from src.indexing import IndexedChunk
from src.vector_store import JsonVectorStore


def test_json_vector_store_add_and_search(tmp_path: Path) -> None:
    store = JsonVectorStore(tmp_path)
    store.add(
        [
            IndexedChunk("1", "tax document", [1.0, 0.0], {"tag_tax": True}),
            IndexedChunk("2", "medical document", [0.0, 1.0], {"tag_medical": True}),
        ]
    )

    results = store.search([1.0, 0.0], limit=1, filters={"tag_tax": True})

    assert len(results) == 1
    assert results[0].id == "1"
