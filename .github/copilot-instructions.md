# Copilot Instructions for code-indxr

## Project Overview
- **Purpose:** Indexes source code files and enables semantic search using vector embeddings (OpenAI or local BGE-small model) and LanceDB for storage.
- **CLI Entrypoint:** `src/cli.py` provides `index` and `search` commands. See [README.md](../README.md) for usage examples.
- **Core Components:**
  - `embedder.py`: Embedding logic, supports OpenAI and local models. Uses `OPENAI_API_KEY` if set, else falls back to local model.
  - `core.py`/`indexer.py`: File discovery, filtering, and reading. Defines `CODE_EXTENSIONS` and `SKIP_PATTERNS` for what to index/ignore.
  - `cli.py`: Orchestrates indexing and search, manages batching, and handles CLI args.

## Key Patterns & Conventions
- **File Filtering:** Only files with extensions in `CODE_EXTENSIONS` are indexed. Files/folders matching `SKIP_PATTERNS` are always ignored.
- **Batching:** Embedding and DB writes are batched for efficiency. See `embed_batch_size` and `write_batch_size` in `cli.py`.
- **Embeddings:**
  - OpenAI model: 1536 dims (`OPENAI_API_KEY` required)
  - Local BGE-small: 384 dims (default)
- **Schema:** Indexed data includes `path`, `content`, `language`, and `vector` fields.
- **Error Handling:** Skips unreadable/oversized files and logs warnings, but continues processing.

## Developer Workflows
- **Install:** `pip install git+https://github.com/ericmaster/code-indxr.git`
- **Index:** `code-index index . --db ./my_index.lancedb`
- **Search:** `code-index search "query" --db ./my_index.lancedb`
- **Local Embeddings:** Install with `pip install 'code-indexer[local]'` for offline mode.
- **Environment:** Set `OPENAI_API_KEY` in `.env` for OpenAI embeddings.

## Integration & Extensibility
- **LanceDB:** Used for vector storage. Table schema is defined in `cli.py`.
- **Embedders:** Add new embedding backends by extending `embedder.py` and updating `get_embedding_function()`.
- **CLI:** Add new commands by extending `cli.py` and updating the `argparse` subparsers.

## References
- [src/cli.py](../src/cli.py): CLI logic, batching, schema
- [src/embedder.py](../src/embedder.py): Embedding selection and logic
- [src/core.py](../src/core.py), [src/indexer.py](../src/indexer.py): File discovery, filtering, and reading
- [README.md](../README.md): Usage examples and install instructions

---
**Edit this file to update project-specific AI agent guidance.**
