from __future__ import annotations

from pathlib import Path

from src.config import Settings
from src.run_config import WorkflowConfig, load_workflow_config


def test_workflow_config_validates_required_file() -> None:
    try:
        WorkflowConfig(task="summarize")
    except ValueError as exc:
        assert "requires files or local_context_folder" in str(exc)
    else:
        raise AssertionError("Expected summarize without context to fail.")


def test_load_workflow_config_from_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "workflow.json"
    config_file.write_text(
        '{"task": "ask", "files": ["data/private/doc.txt"], "question": "What is this?"}',
        encoding="utf-8",
    )
    settings = Settings(app_config_path=config_file)

    workflow = load_workflow_config(settings)

    assert workflow.task == "ask"
    assert workflow.files == [Path("data/private/doc.txt")]
    assert workflow.question == "What is this?"


def test_env_values_override_workflow_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "workflow.json"
    config_file.write_text(
        '{"task": "chat"}',
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "APP_TASK=search\nAPP_QUESTION=fees\nAPP_TAGS=financial,taxes\n",
        encoding="utf-8",
    )
    settings = Settings(app_config_path=config_file)

    workflow = load_workflow_config(settings)

    assert workflow.task == "search"
    assert workflow.question == "fees"
    assert workflow.tags == ["financial", "taxes"]


def test_workflow_config_accepts_context_folder() -> None:
    workflow = WorkflowConfig(task="summarize", local_context_folder=Path("data/private/financial"))

    assert workflow.local_context_folder == Path("data/private/financial")


def test_workflow_config_accepts_single_file_string() -> None:
    workflow = WorkflowConfig(task="summarize", files="data/private/tax_doc.pdf")

    assert workflow.files == [Path("data/private/tax_doc.pdf")]
