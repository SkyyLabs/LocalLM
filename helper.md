# LocalLM Helper

This file is the operational command guide for the project. The preferred daily workflow is:

```bash
python main.py
```

Configure what that command does through `.env` or `config/workflow.json`. Keep `.env`, `config/workflow.json`, `data/private/`, and `data/index/` private.

## 1. First-Time Setup

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
cp config/workflow.example.json config/workflow.json
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
Copy-Item config\workflow.example.json config\workflow.json
```

Install Ollama from:

```text
https://ollama.com
```

Pull a local chat model:

```bash
ollama pull qwen2.5
```

Pull a local embedding model for indexing:

```bash
ollama pull nomic-embed-text
```

## 2. Core Configuration

Edit `.env`:

```env
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=qwen2.5
SYSTEM_PROMPT_PATH=prompts/system_prompt.md
PRIVATE_DATA_DIR=data/private
INDEX_DIR=data/index
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=nomic-embed-text
VECTOR_STORE=chroma
APP_CONFIG_PATH=config/workflow.json
APP_TASK=chat
```

Local mode is the default and should be used for private documents.

Cloud mode:

```env
LLM_PROVIDER=cloud
CLOUD_LLM_BASE_URL=https://api.openai.com/v1
CLOUD_LLM_MODEL=gpt-4o-mini
CLOUD_LLM_API_KEY=your_key_here
```

Cloud mode warns before use and refuses private files unless `APP_YES=true`, `"yes": true`, or `ALLOW_CLOUD_PRIVATE_DOCS=true` is set.

## 3. Run the Configured Workflow

After editing `.env` or `config/workflow.json`, run:

```bash
python main.py
```

This reads Pydantic settings from environment variables and `.env`, then loads `config/workflow.json` if present. Environment variables override the JSON file.

## 4. Configure Tasks With Environment Variables

Start chat:

```env
APP_TASK=chat
```

Summarize a document:

```env
APP_TASK=summarize
APP_FILES=data/private/tax_doc.pdf
```

Ask a question about one document:

```env
APP_TASK=ask
APP_FILES=data/private/bank_statement.pdf
APP_QUESTION=What fees were charged?
```

Ask a question using multiple direct context files:

```env
APP_TASK=ask
APP_FILES=data/private/bank_statement.pdf,data/private/notes.md
APP_QUESTION=What do these files say about monthly cash flow?
```

Ask using every supported file in a local folder, recursively:

```env
APP_TASK=ask
APP_LOCAL_CONTEXT_FOLDER=data/private/financial
APP_QUESTION=What are the recurring expenses across these files?
```

Extract structured JSON:

```env
APP_TASK=extract
APP_FILES=data/private/invoice.pdf
APP_SCHEMA=schemas/example_schema.json
```

Index private documents locally:

```env
APP_TASK=index
APP_PATH=data/private
APP_TAGS=financial,taxes
APP_METADATA=owner=me,year=2026
```

Search the local index:

```env
APP_TASK=search
APP_QUESTION=Find account maintenance fees
APP_TAGS=financial
APP_LIMIT=5
```

Ask over the local index:

```env
APP_TASK=ask-index
APP_QUESTION=Which tax documents mention withholding?
APP_TAGS=taxes
APP_FILTERS=document_type=tax,year=2025
APP_LIMIT=5
```

Then run:

```bash
python main.py
```

## 5. Configure Tasks With `config/workflow.json`

Copy the example once:

```bash
cp config/workflow.example.json config/workflow.json
```

The file contains an active `workflow` block and a `templates` catalog. To run a different task, copy one template object into `workflow`, edit paths/questions, then run `python main.py`.

### Workflow Field Reference

These are the supported keys inside the active `workflow` object:

```json
{
  "task": "chat",
  "files": [],
  "local_context_folder": null,
  "question": null,
  "schema": null,
  "path": "data/private",
  "tags": [],
  "metadata": [],
  "metadata_file": null,
  "filters": [],
  "limit": 5,
  "chunk_size": 1200,
  "overlap": 150,
  "yes": false
}
```

`task`: Which workflow to run. Supported values are `chat`, `ask`, `summarize`, `extract`, `index`, `search`, and `ask-index`.

`files`: One file path or a list of file paths to load directly into context for `ask`, `summarize`, and `extract`. Can leave empty when using `local_context_folder`, `chat`, `index`, `search`, or `ask-index`.

`local_context_folder`: A folder path to traverse recursively for direct context in `ask`, `summarize`, and `extract`. Supported files inside the folder are loaded without creating a RAG index. Can leave `null` when using `files`.

`question`: The question or search text. Required for `ask`, `search`, and `ask-index`. Not used by `chat`, `summarize`, `extract`, or `index`.

`schema`: Path to a JSON schema file for `extract`. Leave `null` for every other task.

`path`: File or folder path to index for `index`. Defaults to `data/private`. Not used by direct context tasks or search tasks.

`tags`: For RAG. Tags to attach during `index`, or tags to filter by during `search` and `ask-index`. For direct context tasks, leave empty.

`metadata`: For RAG. Extra `key=value` metadata to attach during `index`, such as `owner=me` or `year=2026`.

`metadata_file`: For RAG. Path to a JSON metadata map for `index`, usually `schemas/metadata.example.json` or a file you create from it.

`filters`: For RAG. Metadata filters for `search` and `ask-index`, written as `key=value`, such as `document_type=tax` or `year=2025`.

`limit`: For RAG. Maximum number of retrieved chunks for `search` and `ask-index`. It does not limit direct `files` or `local_context_folder` loading.

`chunk_size`: For RAG. Character length for chunks created during `index`, and for direct prompt chunking before sending context to the model.

`overlap`: Character overlap between chunks during `index`. Direct prompt chunking currently uses the app default.

`yes`: Explicitly confirms cloud processing for private files in a single configured workflow. Keep `false` unless you intentionally accept sending private context to the configured cloud provider.

Example summarize config:

```json
{
  "workflow": {
    "task": "summarize",
    "files": ["data/private/tax_doc.pdf"]
  }
}
```

For a single file, this shorter form is also accepted:

```json
{
  "workflow": {
    "task": "summarize",
    "files": "data/private/tax_doc.pdf"
  }
}
```

Example ask config:

```json
{
  "workflow": {
    "task": "ask",
    "files": ["data/private/bank_statement.pdf"],
    "question": "What fees were charged?"
  }
}
```

Example multi-file context config:

```json
{
  "workflow": {
    "task": "ask",
    "files": [
      "data/private/bank_statement.pdf",
      "data/private/notes.md"
    ],
    "question": "What do these files say about monthly cash flow?"
  }
}
```

Example recursive folder context config:

```json
{
  "workflow": {
    "task": "summarize",
    "local_context_folder": "data/private/financial"
  }
}
```

Example local index config:

```json
{
  "workflow": {
    "task": "index",
    "path": "data/private",
    "tags": ["financial", "taxes"],
    "metadata": ["owner=me", "year=2026"],
    "metadata_file": "schemas/metadata.example.json",
    "chunk_size": 1200,
    "overlap": 150
  }
}
```

Example search config:

```json
{
  "workflow": {
    "task": "search",
    "question": "Find account maintenance fees",
    "tags": ["financial"],
    "filters": ["year=2026"],
    "limit": 5
  }
}
```

Example RAG Q&A config:

```json
{
  "workflow": {
    "task": "ask-index",
    "question": "What tax documents mention withholding?",
    "tags": ["taxes"],
    "filters": ["document_type=tax", "year=2025"],
    "limit": 5
  }
}
```

Then run:

```bash
python main.py
```

## 6. Vector Store Options

Default Chroma:

```env
VECTOR_STORE=chroma
```

Optional FAISS:

```bash
pip install ".[faiss]"
```

```env
VECTOR_STORE=faiss
```

Index files are stored in `data/index/` and ignored by Git.

## 7. Privacy Checklist

- Use `LLM_PROVIDER=local` for sensitive documents.
- Keep private files in `data/private/`.
- Treat `data/index/` as sensitive because it contains indexed chunks and embeddings.
- Do not commit `.env` or `config/workflow.json`.
- Do not set `ALLOW_CLOUD_PRIVATE_DOCS=true` unless you intentionally accept cloud processing.
- Remember that a remote `LOCAL_LLM_BASE_URL` is not local privacy.

## 8. Testing

Run:

```bash
.venv/bin/python -m pytest
```

Compile-check:

```bash
.venv/bin/python -m compileall app.py main.py src tests
```
