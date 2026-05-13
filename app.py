from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.chunking import chunk_text
from src.config import load_settings
from src.document_loader import load_document
from src.llm.base import LLMMessage
from src.llm.factory import create_provider
from src.prompts import load_system_prompt
from src.safety import UnsafeCloudProcessingError, enforce_private_document_policy, print_cloud_warning


def build_messages(system_prompt: str, task_prompt: str, document: str | None = None) -> list[LLMMessage]:
    user_parts = [task_prompt]
    if document:
        chunks = chunk_text(document)
        joined_chunks = "\n\n".join(
            f"--- Document chunk {index + 1} ---\n{chunk}" for index, chunk in enumerate(chunks)
        )
        user_parts.append(f"Document content:\n{joined_chunks}")

    return [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content="\n\n".join(user_parts)),
    ]


def run_llm_task(task_prompt: str, file_path: Path | None, assume_yes: bool = False) -> str:
    settings = load_settings()
    if settings.is_cloud:
        print_cloud_warning(file_path)
    enforce_private_document_policy(file_path=file_path, settings=settings, assume_yes=assume_yes)

    document = load_document(file_path) if file_path else None
    system_prompt = load_system_prompt(settings.system_prompt_path)
    provider = create_provider(settings)
    return provider.generate(build_messages(system_prompt, task_prompt, document))


def cmd_ask(args: argparse.Namespace) -> int:
    result = run_llm_task(args.question, args.file, args.yes)
    print(result)
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    result = run_llm_task("Summarize this document clearly and concisely.", args.file, args.yes)
    print(result)
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    prompt = (
        "Extract structured data from this document. Return only valid JSON matching this schema:\n"
        f"{json.dumps(schema, indent=2)}"
    )
    result = run_llm_task(prompt, args.file, args.yes)
    print(result)
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    settings = load_settings()
    if settings.is_cloud:
        print_cloud_warning()
    system_prompt = load_system_prompt(settings.system_prompt_path)
    provider = create_provider(settings)

    print("Chat started. Type 'exit' or 'quit' to stop.")
    history: list[LLMMessage] = [LLMMessage(role="system", content=system_prompt)]
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if user_input.lower() in {"exit", "quit"}:
            return 0
        if not user_input:
            continue
        history.append(LLMMessage(role="user", content=user_input))
        answer = provider.generate(history)
        history.append(LLMMessage(role="assistant", content=answer))
        print(answer)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Privacy-first LLM workflow with local-by-default document processing."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask = subparsers.add_parser("ask", help="Ask a question about a local document.")
    ask.add_argument("--file", type=Path, required=True)
    ask.add_argument("--question", required=True)
    ask.add_argument("--yes", action="store_true", help="Confirm cloud processing for private documents.")
    ask.set_defaults(func=cmd_ask)

    summarize = subparsers.add_parser("summarize", help="Summarize a local document.")
    summarize.add_argument("--file", type=Path, required=True)
    summarize.add_argument("--yes", action="store_true", help="Confirm cloud processing for private documents.")
    summarize.set_defaults(func=cmd_summarize)

    extract = subparsers.add_parser("extract", help="Extract structured data using a JSON schema.")
    extract.add_argument("--file", type=Path, required=True)
    extract.add_argument("--schema", type=Path, required=True)
    extract.add_argument("--yes", action="store_true", help="Confirm cloud processing for private documents.")
    extract.set_defaults(func=cmd_extract)

    chat = subparsers.add_parser("chat", help="Start an interactive chat.")
    chat.set_defaults(func=cmd_chat)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except UnsafeCloudProcessingError as exc:
        print(f"Refusing unsafe cloud processing: {exc}")
        return 2
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
