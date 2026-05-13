from __future__ import annotations

import json
from pathlib import Path

from src.run_config import WorkflowConfig


def test_workflow_example_contains_all_task_templates() -> None:
    data = json.loads(Path("config/workflow.example.json").read_text(encoding="utf-8"))

    assert WorkflowConfig(**data["workflow"]).task == "chat"
    template_tasks = {template["task"] for template in data["templates"].values()}
    assert template_tasks == {"ask", "summarize", "extract", "chat", "index", "search", "ask-index"}
