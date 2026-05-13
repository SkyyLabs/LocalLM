# Privacy Design

This project is local-first by default. Files under `data/private/` are assumed to contain sensitive content such as financial records, medical documents, personal notes, tax files, and identity-related material.

## Default Protections

- `LLM_PROVIDER=local` is the default.
- Local mode sends prompts to Ollama on your machine.
- Cloud API keys are read only from environment variables.
- Files in `data/private/` are not committed to Git.
- If cloud mode is enabled and a private file is selected, the CLI refuses to continue unless you explicitly confirm with `--yes` or set `ALLOW_CLOUD_PRIVATE_DOCS=true`.

## What Local Mode Means

Local mode uses Ollama's local HTTP API. Your document text is sent to `http://localhost:11434` by default. That should stay on your machine, assuming Ollama is running locally and you have not configured a remote Ollama host.

## Cloud Mode Risk

Cloud mode sends prompt and document content to the configured OpenAI-compatible endpoint. Only use it for documents you are comfortable sharing with that provider under its terms, retention policy, and security model.

## Practical Recommendations

- Keep `LLM_PROVIDER=local` for sensitive documents.
- Use cloud mode only for non-sensitive documents or after redaction.
- Review `.env` before running commands.
- Do not place real private documents in public repositories.
- Consider full-disk encryption and local backups for `data/private/`.
