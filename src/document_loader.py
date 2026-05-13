from __future__ import annotations

import csv
from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".csv"}


def load_document(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    if not path.is_file():
        raise ValueError(f"Expected a file path, got: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported file type '{suffix}'. Supported types: {supported}")

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".csv":
        return _read_csv(path)
    if suffix == ".pdf":
        return _read_pdf(path)

    raise ValueError(f"Unsupported file type: {suffix}")


def _read_csv(path: Path) -> str:
    rows: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            rows.append(", ".join(row))
    return "\n".join(rows)


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF support requires pypdf. Install dependencies first.") from exc

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page.strip() for page in pages if page.strip())
