from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from src.chunking import chunk_text
from src.config import load_settings
from src.document_loader import load_document
from src.embeddings import LocalOllamaEmbeddingProvider
from src.indexing import build_index_chunks
from src.metadata import Metadata, parse_key_value_pairs
from src.llm.base import LLMMessage
from src.llm.factory import create_provider
from src.prompts import load_system_prompt
from src.run_config import WorkflowConfig, load_workflow_config
from src.safety import UnsafeCloudProcessingError, enforce_private_document_policy, print_cloud_warning
from src.vector_store import SearchResult, create_vector_store


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


def format_search_results(results: list[SearchResult]) -> str:
    if not results:
        return "No matching chunks found."

    lines: list[str] = []
    for index, result in enumerate(results, start=1):
        source = result.metadata.get("source", "unknown")
        chunk_index = result.metadata.get("chunk_index", "?")
        tags = result.metadata.get("tags", "")
        tag_text = f" tags={tags}" if tags else ""
        lines.append(
            f"[{index}] score={result.score:.4f} source={source} chunk={chunk_index}{tag_text}\n"
            f"{result.text}"
        )
    return "\n\n".join(lines)


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


def cmd_index(args: argparse.Namespace) -> int:
    settings = load_settings()
    if settings.is_cloud:
        raise UnsafeCloudProcessingError(
            "Indexing is local-only. Set LLM_PROVIDER=local before indexing private documents."
        )

    embedder = LocalOllamaEmbeddingProvider(settings.local_base_url, settings.local_embedding_model)
    metadata = parse_key_value_pairs(args.metadata)
    metadata_by_file = {}
    if args.metadata_file:
        from src.metadata import load_metadata_file

        metadata_by_file = load_metadata_file(args.metadata_file)

    chunks = build_index_chunks(
        path=args.path,
        embedder=embedder,
        tags=args.tag,
        cli_metadata=metadata,
        metadata_by_file=metadata_by_file,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    store = create_vector_store(settings.vector_store, settings.index_dir)
    store.add(chunks)
    print(f"Indexed {len(chunks)} chunks from {args.path} into {settings.vector_store} at {settings.index_dir}.")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    settings = load_settings()
    embedder = LocalOllamaEmbeddingProvider(settings.local_base_url, settings.local_embedding_model)
    filters = build_filters(args.filter, args.tag)
    store = create_vector_store(settings.vector_store, settings.index_dir)
    query = getattr(args, "query", None) or getattr(args, "question", None)
    results = store.search(embedder.embed(query), limit=args.limit, filters=filters)
    print(format_search_results(results))
    return 0


def cmd_ask_index(args: argparse.Namespace) -> int:
    settings = load_settings()
    if settings.is_cloud:
        print_cloud_warning()

    embedder = LocalOllamaEmbeddingProvider(settings.local_base_url, settings.local_embedding_model)
    filters = build_filters(args.filter, args.tag)
    store = create_vector_store(settings.vector_store, settings.index_dir)
    results = store.search(embedder.embed(args.question), limit=args.limit, filters=filters)

    for result in results:
        source = result.metadata.get("source")
        if isinstance(source, str):
            enforce_private_document_policy(file_path=Path(source), settings=settings, assume_yes=args.yes)

    context = format_search_results(results)
    system_prompt = load_system_prompt(settings.system_prompt_path)
    provider = create_provider(settings)
    prompt = (
        "Answer the question using only the retrieved local document chunks below. "
        "If the chunks do not contain the answer, say so.\n\n"
        f"Question: {args.question}\n\nRetrieved chunks:\n{context}"
    )
    print(provider.generate(build_messages(system_prompt, prompt)))
    return 0


def build_filters(filter_values: list[str] | None, tags: list[str] | None) -> Metadata:
    filters = parse_key_value_pairs(filter_values)
    for tag in tags or []:
        normalized = "".join(character if character.isalnum() else "_" for character in tag.strip().lower()).strip("_")
        if normalized:
            filters[f"tag_{normalized}"] = True
    return filters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Privacy-first LLM workflow with local-by-default document processing."
    )
    subparsers = parser.add_subparsers(dest="command")

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

    index = subparsers.add_parser("index", help="Locally index documents for RAG search.")
    index.add_argument("--path", type=Path, default=Path("data/private"), help="File or folder to index.")
    index.add_argument("--tag", action="append", help="Tag to attach to indexed chunks. Can be repeated.")
    index.add_argument("--metadata", action="append", help="Metadata as key=value. Can be repeated.")
    index.add_argument("--metadata-file", type=Path, help="JSON metadata map keyed by file path or file name.")
    index.add_argument("--chunk-size", type=int, default=1200)
    index.add_argument("--overlap", type=int, default=150)
    index.set_defaults(func=cmd_index)

    search = subparsers.add_parser("search", help="Search the local vector index.")
    search.add_argument("--query", required=True)
    search.add_argument("--tag", action="append", help="Require a tag. Can be repeated.")
    search.add_argument("--filter", action="append", help="Metadata filter as key=value. Can be repeated.")
    search.add_argument("--limit", type=int, default=5)
    search.set_defaults(func=cmd_search)

    ask_index = subparsers.add_parser("ask-index", help="Ask a question over locally indexed documents.")
    ask_index.add_argument("--question", required=True)
    ask_index.add_argument("--tag", action="append", help="Require a tag. Can be repeated.")
    ask_index.add_argument("--filter", action="append", help="Metadata filter as key=value. Can be repeated.")
    ask_index.add_argument("--limit", type=int, default=5)
    ask_index.add_argument("--yes", action="store_true", help="Confirm cloud processing for private retrieved chunks.")
    ask_index.set_defaults(func=cmd_ask_index)

    return parser


def run_configured_workflow() -> int:
    settings = load_settings()
    workflow = load_workflow_config(settings)
    namespace = _workflow_to_namespace(workflow)
    handlers = {
        "ask": cmd_ask,
        "summarize": cmd_summarize,
        "extract": cmd_extract,
        "chat": cmd_chat,
        "index": cmd_index,
        "search": cmd_search,
        "ask-index": cmd_ask_index,
    }
    return handlers[workflow.task](namespace)


def _workflow_to_namespace(workflow: WorkflowConfig) -> SimpleNamespace:
    return SimpleNamespace(
        file=workflow.file,
        question=workflow.question,
        schema=workflow.schema_path,
        path=workflow.path,
        tag=workflow.tags,
        metadata=workflow.metadata,
        metadata_file=workflow.metadata_file,
        filter=workflow.filters,
        limit=workflow.limit,
        chunk_size=workflow.chunk_size,
        overlap=workflow.overlap,
        yes=workflow.yes,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command is None:
            return run_configured_workflow()
        return args.func(args)
    except UnsafeCloudProcessingError as exc:
        print(f"Refusing unsafe cloud processing: {exc}")
        return 2
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
