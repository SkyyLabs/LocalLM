from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.config import Settings, TaskName


class WorkflowConfig(BaseModel):
    """File-backed task config used when running plain `python main.py`."""

    model_config = ConfigDict(extra="forbid")

    task: TaskName = "chat"
    file: Path | None = None
    question: str | None = None
    schema_path: Path | None = Field(default=None, alias="schema")
    path: Path = Path("data/private")
    tags: list[str] = Field(default_factory=list)
    metadata: list[str] = Field(default_factory=list)
    metadata_file: Path | None = None
    filters: list[str] = Field(default_factory=list)
    limit: int = 5
    chunk_size: int = 1200
    overlap: int = 150
    yes: bool = False

    @model_validator(mode="after")
    def validate_task_inputs(self) -> "WorkflowConfig":
        if self.task in {"ask", "summarize", "extract"} and self.file is None:
            raise ValueError(f"task '{self.task}' requires a file.")
        if self.task in {"ask", "search", "ask-index"} and not self.question:
            raise ValueError(f"task '{self.task}' requires a question.")
        if self.task == "extract" and self.schema_path is None:
            raise ValueError("task 'extract' requires a schema.")
        return self


def load_workflow_config(settings: Settings) -> WorkflowConfig:
    values = _load_settings_defaults(settings) if not settings.app_config_path.exists() else {}
    file_values = _load_config_file(settings.app_config_path)
    explicit_env_values = _load_explicit_env_task_values()
    return WorkflowConfig(**{**values, **file_values, **explicit_env_values})


def _load_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Workflow config must be a JSON object: {path}")
    return data


def _load_settings_defaults(settings: Settings) -> dict[str, Any]:
    values: dict[str, Any] = {"task": settings.app_task}
    optional_values = {
        "file": settings.app_file,
        "question": settings.app_question,
        "schema": settings.app_schema,
        "path": settings.app_path,
        "tags": settings.app_tags,
        "metadata": settings.app_metadata,
        "metadata_file": settings.app_metadata_file,
        "filters": settings.app_filters,
        "limit": settings.app_limit,
        "chunk_size": settings.app_chunk_size,
        "overlap": settings.app_overlap,
        "yes": settings.app_yes,
    }
    for key, value in optional_values.items():
        if value is None or value == "" or value == []:
            continue
        else:
            values[key] = value
    return values


def _load_explicit_env_task_values(env_path: Path = Path(".env")) -> dict[str, Any]:
    raw_values = {**_read_env_file(env_path), **os.environ}
    alias_map = {
        "task": ("APP_TASK", "TASK"),
        "file": ("APP_FILE", "TASK_FILE"),
        "question": ("APP_QUESTION", "TASK_QUESTION"),
        "schema": ("APP_SCHEMA", "TASK_SCHEMA"),
        "path": ("APP_PATH", "TASK_PATH"),
        "tags": ("APP_TAGS", "TASK_TAGS"),
        "metadata": ("APP_METADATA", "TASK_METADATA"),
        "metadata_file": ("APP_METADATA_FILE", "TASK_METADATA_FILE"),
        "filters": ("APP_FILTERS", "TASK_FILTERS"),
        "limit": ("APP_LIMIT", "TASK_LIMIT"),
        "chunk_size": ("APP_CHUNK_SIZE", "TASK_CHUNK_SIZE"),
        "overlap": ("APP_OVERLAP", "TASK_OVERLAP"),
        "yes": ("APP_YES", "TASK_YES"),
    }
    values: dict[str, Any] = {}
    for field, aliases in alias_map.items():
        for alias in aliases:
            if alias in raw_values and raw_values[alias] != "":
                values[field] = _coerce_env_value(field, raw_values[alias])
                break
    return values


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _coerce_env_value(field: str, value: str) -> Any:
    if field in {"tags", "metadata", "filters"}:
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            if not isinstance(parsed, list):
                raise ValueError(f"{field} must be a list.")
            return parsed
        return [item.strip() for item in stripped.split(",") if item.strip()]
    if field in {"limit", "chunk_size", "overlap"}:
        return int(value)
    if field == "yes":
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return value
