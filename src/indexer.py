import os
import sys
import argparse
from pathlib import Path
import lancedb
from .embedder import get_embedding_function
from .core import read_files

def index_codebase(db_path: str, code_dir: str, table_name: str = "code"):
    """Index a code directory into LanceDB."""
    db = lancedb.connect(db_path)
    chunks = read_files(Path(code_dir))

    if not chunks:
        print("⚠️ No code files found. Check directory and permissions.")
        return

    # Precompute embeddings for all chunks
    ef = get_embedding_function()
    texts = [chunk["content"] for chunk in chunks]
    try:
        vectors = ef(texts)
        for chunk, vec in zip(chunks, vectors):
            chunk["vector"] = vec
        tbl = db.create_table(
            table_name,
            data=chunks,
            mode="overwrite"
        )
        print(f"✅ Indexed {len(chunks)} files into table '{table_name}' at {db_path}")
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        raise

def search_code(db_path: str, query: str, table_name: str = "code", limit: int = 5):
    """Search indexed codebase using natural language."""
    ef = get_embedding_function()
    query_vec = ef([query])[0]
    db = lancedb.connect(db_path)
    tbl = db.open_table(table_name)
    results = tbl.search(query_vec).limit(limit).to_pandas()
    return results[["path", "content", "_distance"]]
