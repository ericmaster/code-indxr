# Code Indexer

## Install

### Standard (with OpenAI support)
```bash
pip install git+https://github.com/ericmaster/code-indxr.git
```

### Local Embeddings (Offline Mode)
To use only local embeddings (no OpenAI/cloud required):
```bash
pip install 'git+https://github.com/ericmaster/code-indxr.git#egg=code-indexer[local]'
```
This installs only the dependencies needed for local embedding (sentence-transformers, torch).


### Local Development Install
To install in editable/development mode from a local path:
```bash
pip install -e .
```
For local embeddings only (offline mode):
```bash
pip install -e .[local]
```

## Usage

1. Index your codebase:
```bash
code-index index . --db ./my_index.lancedb
```

2. Search it:
```bash
code-index search "database connection logic" --db ./my_index.lancedb
```