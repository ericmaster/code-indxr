# Code Indexer

## Install
```bash
pip install git+https://github.com/ericmaster/code-indxr.git
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