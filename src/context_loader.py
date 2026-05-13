from __future__ import annotations

from pathlib import Path

from src.document_loader import SUPPORTED_EXTENSIONS, load_document


def resolve_context_files(files: list[Path] | None, local_context_folder: Path | None) -> list[Path]:
    """Resolve explicit files plus every supported file inside a context folder."""
    resolved: list[Path] = []
    seen: set[Path] = set()

    for file_path in files or []:
        if not file_path.exists():
            raise FileNotFoundError(f"Context file not found: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Context path in files must be a file: {file_path}")
        _append_once(resolved, seen, file_path)

    if local_context_folder is not None:
        if not local_context_folder.exists():
            raise FileNotFoundError(f"Context folder not found: {local_context_folder}")
        if not local_context_folder.is_dir():
            raise ValueError(f"local_context_folder must be a folder: {local_context_folder}")
        for file_path in sorted(local_context_folder.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                _append_once(resolved, seen, file_path)

    return resolved


def load_context_documents(files: list[Path] | None, local_context_folder: Path | None) -> tuple[str | None, list[Path]]:
    context_files = resolve_context_files(files, local_context_folder)
    return load_resolved_context_documents(context_files), context_files


def load_resolved_context_documents(context_files: list[Path]) -> str | None:
    documents: list[str] = []
    for file_path in context_files:
        documents.append(f"--- Source: {file_path} ---\n{load_document(file_path)}")
    return "\n\n".join(documents) if documents else None



def _append_once(resolved: list[Path], seen: set[Path], file_path: Path) -> None:
    normalized = file_path.resolve()
    if normalized in seen:
        return
    seen.add(normalized)
    resolved.append(file_path)
