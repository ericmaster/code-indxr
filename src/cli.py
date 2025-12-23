import argparse
import sys
import pandas as pd
import lancedb
from .embedder import get_embedding_function
from .core import read_files

def index_codebase(db_path: str, code_dir: str, table_name: str = "code"):
    from pathlib import Path
    chunks = read_files(Path(code_dir))
    if not chunks:
        print("❌ No code files found.")
        return

    ef = get_embedding_function()
    ndims = getattr(ef, "ndims", 384)

    # ✅ Manually embed and add 'vector' column
    print(f"Embedding {len(chunks)} files...")
    embedded_chunks = []
    for chunk in chunks:
        vector = ef([chunk["content"]])[0]
        embedded_chunks.append({
            "path": chunk["path"],
            "content": chunk["content"],
            "language": chunk["language"],
            "vector": vector,
        })

    # ✅ Explicit schema
    schema = pa.schema([
        pa.field("path", pa.string()),
        pa.field("content", pa.string()),
        pa.field("language", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), ndims)),
    ])

    db = lancedb.connect(db_path)
    tbl = db.create_table(table_name, data=embedded_chunks, schema=schema, mode="overwrite")
    print(f"✅ Indexed with {ndims}-dim vectors.")

def search_code(db_path: str, query: str, table_name: str = "code", limit: int = 5):
    ef = get_embedding_function()
    query_vec = ef([query])[0]

    db = lancedb.connect(db_path)
    tbl = db.open_table(table_name)
    results = tbl.search(query_vec).limit(limit).to_pandas()

    if results.empty:
        print("No results found.")
        return

    print("\n🔍 Search Results:\n")
    for _, row in results.iterrows():
        print(f"📄 {row['path']}")
        print("-" * 60)
        lines = row["content"].splitlines()
        print("\n".join(lines[:8]))
        if len(lines) > 8:
            print("... (truncated)")
        print("=" * 60 + "\n")

def main():
    parser = argparse.ArgumentParser(prog="code-index")
    subparsers = parser.add_subparsers(dest="command", required=True)

    idx = subparsers.add_parser("index", help="Index a code directory")
    idx.add_argument("code_dir", help="Path to source code directory")
    idx.add_argument("--db", default="./code_index.lancedb", help="LanceDB path")

    srch = subparsers.add_parser("search", help="Search indexed code")
    srch.add_argument("query", help="Natural language query")
    srch.add_argument("--db", default="./code_index.lancedb", help="LanceDB path")
    srch.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    if args.command == "index":
        index_codebase(args.db, args.code_dir)
    elif args.command == "search":
        search_code(args.db, args.query, limit=args.limit)