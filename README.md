# LocalLM Privacy Workflow

A production-ready, privacy-first Python repo for running LLM tasks against local documents. It defaults to local Ollama models so private files stay on your machine unless you explicitly choose cloud mode.

## What This Repo Does

- Runs document tasks through either a local LLM or an OpenAI-compatible cloud LLM.
- Uses `LLM_PROVIDER=local` by default.
- Reads `.txt`, `.md`, `.pdf`, and `.csv` files.
- Loads an editable system prompt from `prompts/system_prompt.md`.
- Provides CLI commands for asking questions, summarizing, extraction, and chat.
- Includes a RAG-ready structure with chunking and folders for private data, schemas, prompts, docs, source, and tests.

## Why Local LLMs Matter

Financial records, medical documents, tax files, personal notes, and identity documents can contain information you should not send to third parties by accident. This project makes local processing the default and blocks cloud processing for files in `data/private/` unless you explicitly confirm it.

## Project Structure

```text
.
├── app.py
├── data/
│   ├── output/
│   └── private/
├── docs/
│   └── privacy.md
├── prompts/
│   └── system_prompt.md
├── schemas/
│   └── example_schema.json
├── src/
│   ├── chunking.py
│   ├── config.py
│   ├── document_loader.py
│   ├── prompts.py
│   ├── safety.py
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
```

Install Ollama from [https://ollama.com](https://ollama.com), then start it if it is not already running.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
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

Files in `data/private/` are considered sensitive. If `LLM_PROVIDER=cloud` and you try to process a file from that folder, the CLI refuses by default.

To explicitly allow a single command:

```bash
python app.py summarize --file data/private/tax_doc.pdf --yes
```

For non-interactive automation, set:

```env
ALLOW_CLOUD_PRIVATE_DOCS=true
```

Only do this if you accept that document text may be sent to the configured cloud provider.

## Edit the Prompt

Edit:

```text
prompts/system_prompt.md
```

The app automatically loads this file for every request. You can add instructions for summarization, extraction, rewriting, financial analysis, or question answering without changing Python code.

## CLI Examples

Ask a question:

```bash
python app.py ask --file data/private/bank_statement.pdf --question "Summarize this document"
```

Summarize:

```bash
python app.py summarize --file data/private/tax_doc.pdf
```

Extract JSON using a schema:

```bash
python app.py extract --file data/private/invoice.pdf --schema schemas/example_schema.json
```

Start chat:

```bash
python app.py chat
```

## RAG-Ready Design

This repo includes simple chunking in `src/chunking.py`. Today, chunks are passed directly into the selected LLM. This keeps the first version simple and avoids unnecessary infrastructure.

Future extensions:

- Local embeddings with Ollama embedding models.
- Local vector stores such as SQLite, Chroma, LanceDB, or FAISS.
- Optional cloud embeddings for non-sensitive documents.
- Per-document metadata, tags, and retrieval filters.
- A local-only indexing command for `data/private/`.

## Security Notes

- `.env` is ignored by Git.
- `data/private/*` is ignored by Git.
- Local mode can still leak data if `LOCAL_LLM_BASE_URL` points to a remote server.
- Cloud mode sends document content to the configured provider.
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

### PDF text is empty

Some PDFs are scanned images. This repo extracts embedded text only. Add OCR later with tools such as Tesseract for scanned documents.

### Cloud mode refuses private files

This is intentional. Use local mode or explicitly pass `--yes` after reviewing the risk.

## Tests

```bash
pytest
```
