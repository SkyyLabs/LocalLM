from __future__ import annotations

from pathlib import Path

from src.config import Settings


class UnsafeCloudProcessingError(RuntimeError):
    pass


def is_private_path(path: Path, private_dir: Path) -> bool:
    resolved_path = path.resolve()
    resolved_private_dir = private_dir.resolve()
    return resolved_path == resolved_private_dir or resolved_private_dir in resolved_path.parents


def enforce_private_document_policy(
    *,
    file_path: Path | None,
    settings: Settings,
    assume_yes: bool = False,
) -> None:
    if file_path is None:
        return
    if settings.llm_provider != "cloud":
        return
    if not is_private_path(file_path, settings.private_data_dir):
        return
    if settings.allow_cloud_private_docs or assume_yes:
        return

    raise UnsafeCloudProcessingError(
        "Cloud mode is enabled and this file is inside the private data directory. "
        "Re-run with --yes or set ALLOW_CLOUD_PRIVATE_DOCS=true only if you explicitly "
        "accept sending this document to a cloud provider."
    )


def print_cloud_warning(file_path: Path | None = None) -> None:
    target = f" for {file_path}" if file_path else ""
    print(
        "WARNING: Cloud LLM mode is enabled"
        f"{target}. Document content may leave this device and be processed by a third party."
    )
