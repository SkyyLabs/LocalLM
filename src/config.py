from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ProviderName = Literal["local", "cloud"]
VectorStoreName = Literal["auto", "chroma", "faiss"]
TaskName = Literal["ask", "summarize", "extract", "chat", "index", "search", "ask-index"]


class Settings(BaseSettings):
    """Environment-backed runtime settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        enable_decoding=False,
    )

    llm_provider: ProviderName = Field(default="local", validation_alias="LLM_PROVIDER")
    local_base_url: str = Field(default="http://localhost:11434", validation_alias="LOCAL_LLM_BASE_URL")
    local_model: str = Field(default="qwen2.5", validation_alias="LOCAL_LLM_MODEL")
    cloud_base_url: str = Field(default="https://api.openai.com/v1", validation_alias="CLOUD_LLM_BASE_URL")
    cloud_model: str = Field(default="gpt-4o-mini", validation_alias="CLOUD_LLM_MODEL")
    cloud_api_key: str | None = Field(default=None, validation_alias="CLOUD_LLM_API_KEY")

    system_prompt_path: Path = Field(default=Path("prompts/system_prompt.md"), validation_alias="SYSTEM_PROMPT_PATH")
    private_data_dir: Path = Field(default=Path("data/private"), validation_alias="PRIVATE_DATA_DIR")
    index_dir: Path = Field(default=Path("data/index"), validation_alias="INDEX_DIR")
    allow_cloud_private_docs: bool = Field(default=False, validation_alias="ALLOW_CLOUD_PRIVATE_DOCS")

    embedding_provider: Literal["local"] = Field(default="local", validation_alias="EMBEDDING_PROVIDER")
    local_embedding_model: str = Field(default="nomic-embed-text", validation_alias="LOCAL_EMBEDDING_MODEL")
    vector_store: VectorStoreName = Field(default="chroma", validation_alias="VECTOR_STORE")

    app_config_path: Path = Field(default=Path("config/workflow.json"), validation_alias="APP_CONFIG_PATH")
    app_task: TaskName = Field(default="chat", validation_alias=AliasChoices("APP_TASK", "TASK"))
    app_files: list[Path] = Field(default_factory=list, validation_alias=AliasChoices("APP_FILES", "TASK_FILES"))
    app_local_context_folder: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("APP_LOCAL_CONTEXT_FOLDER", "TASK_LOCAL_CONTEXT_FOLDER"),
    )
    app_question: str | None = Field(default=None, validation_alias=AliasChoices("APP_QUESTION", "TASK_QUESTION"))
    app_schema: Path | None = Field(default=None, validation_alias=AliasChoices("APP_SCHEMA", "TASK_SCHEMA"))
    app_path: Path = Field(default=Path("data/private"), validation_alias=AliasChoices("APP_PATH", "TASK_PATH"))
    app_tags: list[str] = Field(default_factory=list, validation_alias=AliasChoices("APP_TAGS", "TASK_TAGS"))
    app_metadata: list[str] = Field(default_factory=list, validation_alias=AliasChoices("APP_METADATA", "TASK_METADATA"))
    app_metadata_file: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("APP_METADATA_FILE", "TASK_METADATA_FILE"),
    )
    app_filters: list[str] = Field(default_factory=list, validation_alias=AliasChoices("APP_FILTERS", "TASK_FILTERS"))
    app_limit: int = Field(default=5, validation_alias=AliasChoices("APP_LIMIT", "TASK_LIMIT"))
    app_chunk_size: int = Field(default=1200, validation_alias=AliasChoices("APP_CHUNK_SIZE", "TASK_CHUNK_SIZE"))
    app_overlap: int = Field(default=150, validation_alias=AliasChoices("APP_OVERLAP", "TASK_OVERLAP"))
    app_yes: bool = Field(default=False, validation_alias=AliasChoices("APP_YES", "TASK_YES"))

    @property
    def is_cloud(self) -> bool:
        return self.llm_provider == "cloud"

    @field_validator("local_base_url", "cloud_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("app_files", "app_tags", "app_metadata", "app_filters", mode="before")
    @classmethod
    def parse_list_env(cls, value: object) -> object:
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return value
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value


def load_settings(env_file: Path | None = Path(".env")) -> Settings:
    if env_file is None:
        return Settings(_env_file=None)
    return Settings(_env_file=env_file)
