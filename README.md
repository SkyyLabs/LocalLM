# LocalLM Privacy Workflow

A production-ready, privacy-first Python repo for running LLM tasks against local documents. It defaults to local Ollama models so private files stay on your machine unless you explicitly choose cloud mode.

## What This Repo Does

- Runs document tasks through either a local LLM or an OpenAI-compatible cloud LLM.
- Uses `LLM_PROVIDER=local` by default.
- Reads `.txt`, `.md`, `.pdf`, and `.csv` files.
- Loads an editable system prompt from `prompts/system_prompt.md`.
- Runs from `python main.py` using `.env` or `config/workflow.json`.
- Keeps workflow details out of command-line arguments.
- Includes local RAG indexing with Ollama embeddings, Chroma by default, optional FAISS, metadata, tags, and filters.

## Why Local LLMs Matter

Financial records, medical documents, tax files, personal notes, and identity documents can contain information you should not send to third parties by accident. This project makes local processing the default and blocks cloud processing for files in `data/private/` unless you explicitly confirm it.

## Project Structure

```text
.
├── app.py
├── config/
│   └── workflow.example.json
├── data/
│   ├── index/
│   ├── output/
│   └── private/
├── docs/
│   └── privacy.md
├── helper.md
├── main.py
├── prompts/
│   └── system_prompt.md
├── schemas/
│   └── example_schema.json
├── src/
│   ├── chunking.py
│   ├── config.py
│   ├── document_loader.py
│   ├── embeddings.py
│   ├── indexing.py
│   ├── metadata.py
│   ├── prompts.py
│   ├── safety.py
│   ├── vector_store.py
│   └── llm/
└── tests/
```

## Setup

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
cp config/workflow.example.json config/workflow.json
```

Install Ollama from [https://ollama.com](https://ollama.com), then start it if it is not already running.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
Copy-Item config\workflow.example.json config\workflow.json
```

Install Ollama from [https://ollama.com](https://ollama.com). If script activation is blocked, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
cp config/workflow.example.json config/workflow.json
```

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Pull Local Models

Choose one or more:

```bash
ollama pull qwen2.5
ollama pull llama3
ollama pull mistral
ollama pull deepseek-r1
```

Configure the default model in `.env`:

```env
LOCAL_LLM_MODEL=qwen2.5
```

For local RAG indexing, pull an embedding model:

```bash
ollama pull nomic-embed-text
```

Then configure:

```env
LOCAL_EMBEDDING_MODEL=nomic-embed-text
VECTOR_STORE=chroma
INDEX_DIR=data/index
```

## Configure Local vs Cloud

Local mode is the default:

```env
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=qwen2.5
```

Cloud mode is optional and uses an OpenAI-compatible API:

```env
LLM_PROVIDER=cloud
CLOUD_LLM_BASE_URL=https://api.openai.com/v1
CLOUD_LLM_MODEL=gpt-4o-mini
CLOUD_LLM_API_KEY=your_api_key_here
```

Cloud keys are never hardcoded. Do not commit `.env`.

## Privacy Guardrail

Files in `data/private/` are considered sensitive. If `LLM_PROVIDER=cloud` and the configured workflow tries to process a file from that folder, the app refuses by default.

For non-interactive automation, set:

```env
ALLOW_CLOUD_PRIVATE_DOCS=true
```

For a single configured workflow, set `APP_YES=true` or `"yes": true` in `config/workflow.json`. Only do this if you accept that document text may be sent to the configured cloud provider.

## Edit the Prompt

Edit:

```text
prompts/system_prompt.md
```

The app automatically loads this file for every request. You can add instructions for summarization, extraction, rewriting, financial analysis, or question answering without changing Python code.

## Recommended Workflow

Configure `.env` or `config/workflow.json`, then run:

```bash
python main.py
```

See [helper.md](helper.md) for the complete command and configuration guide.

Example `.env` task:

```env
APP_TASK=summarize
APP_FILES=data/private/tax_doc.pdf
```

Example `config/workflow.json`:

```json
{
  "task": "ask",
  "files": ["data/private/bank_statement.pdf"],
  "question": "What fees were charged?"
}
```

Then:

```bash
python main.py
```

## Local RAG Indexing

Indexing is local-only. If `LLM_PROVIDER=cloud`, an `index` workflow refuses to run. Embeddings are generated with Ollama and persisted under `data/index/`, which is ignored by Git.

## Direct Multi-File Context Without RAG

For direct document workflows, use `files` for one or more explicit files:

```json
{
  "task": "ask",
  "files": [
    "data/private/bank_statement.pdf",
    "data/private/notes.md"
  ],
  "question": "What do these files say about monthly cash flow?"
}
```

For a single file, `files` can be either a string or a list.

Or use `local_context_folder` to recursively load every supported file inside a folder:

```json
{
  "task": "summarize",
  "local_context_folder": "data/private/financial"
}
```

You can use `files`, `local_context_folder`, or both. This does not create a vector index; all loaded context is sent directly to the selected model, so keep the total content small enough for the model's context window.

Index all private documents by configuring:

```json
{
  "task": "index",
  "path": "data/private",
  "tags": ["financial"],
  "metadata": ["owner=me"]
}
```

Index with per-document metadata:

```json
{
  "task": "index",
  "path": "data/private",
  "metadata_file": "schemas/metadata.example.json"
}
```

Search the local index:

```json
{
  "task": "search",
  "question": "Find bank fees from March",
  "tags": ["financial"],
  "limit": 5
}
```

Ask over indexed documents:

```json
{
  "task": "ask-index",
  "question": "Which documents mention account maintenance fees?",
  "tags": ["financial"]
}
```

Filter by metadata:

```json
{
  "task": "search",
  "question": "tax withholding",
  "filters": ["document_type=tax", "year=2025"]
}
```

### Vector Stores

The default vector store is Chroma:

```env
VECTOR_STORE=chroma
```

FAISS is also supported:

```bash
pip install ".[faiss]"
```

```env
VECTOR_STORE=faiss
```

Cloud embeddings are intentionally not enabled by default. Add them only for non-sensitive workflows after reviewing the provider's data retention and security policies.

## Security Notes

- `.env` is ignored by Git.
- `data/private/*` is ignored by Git.
- `data/index/*` is ignored by Git.
- Local mode can still leak data if `LOCAL_LLM_BASE_URL` points to a remote server.
- Cloud mode sends document content to the configured provider.
- `ask-index` can send retrieved private chunks to a cloud LLM if `LLM_PROVIDER=cloud`; it requires `APP_YES=true`, `"yes": true`, or `ALLOW_CLOUD_PRIVATE_DOCS=true` for private sources.
- This project is not a substitute for legal, medical, tax, or financial advice.

## Troubleshooting

### Ollama is not reachable

Make sure Ollama is running:

```bash
ollama list
```

Check `.env`:

```env
LOCAL_LLM_BASE_URL=http://localhost:11434
```

### Model not found

Pull it:

```bash
ollama pull qwen2.5
```

For embeddings:

```bash
ollama pull nomic-embed-text
```

### PDF text is empty

Some PDFs are scanned images. This repo extracts embedded text only. Add OCR later with tools such as Tesseract for scanned documents.

### Cloud mode refuses private files

This is intentional. Use local mode or explicitly set `APP_YES=true` or `"yes": true` after reviewing the risk.

### Chroma is not installed

Install dependencies:

```bash
pip install -r requirements.txt
```

Or use FAISS:

```bash
pip install ".[faiss]"
```

## Tests

```bash
pytest
```
