import argparse
import sys
import pandas as pd
import lancedb
from .embedder import get_embedding_function
from .core import read_files
import pyarrow as pa
import lancedb
from tqdm import tqdm

def index_codebase(db_path: str, code_dir: str, table_name: str = "code", embed_batch_size: int = 64, write_batch_size: int = 512):
    from pathlib import Path
    import pandas as pd
    import gc

    ef = get_embedding_function()
    ndims = getattr(ef, "ndims", 384)

    schema = pa.schema([
        pa.field("path", pa.string()),
        pa.field("content", pa.string()),
        pa.field("language", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), ndims)),
    ])

    db = lancedb.connect(db_path)
    tbl = db.create_table(table_name, schema=schema, mode="overwrite")

    # Get all file paths first
    all_files = []
    for file_path in Path(code_dir).rglob("*"):
        if file_path.is_file():
            MAX_FILE_SIZE = 1024 * 1024  # 1 MB
            if file_path.stat().st_size > MAX_FILE_SIZE:
                continue  # skip huge minified/vendor files
            from .core import should_skip, CODE_EXTENSIONS
            if file_path.suffix in CODE_EXTENSIONS and not should_skip(file_path):
                all_files.append(file_path)

    if not all_files:
        print("❌ No code files found.")
        return

    print(f"Found {len(all_files)} files.")
    print(f"Embedding in batches of {embed_batch_size}, writing every {write_batch_size} files...")

    # Buffer for writing
    write_buffer = []
    total_written = 0

    # Embed in small batches (for model efficiency)
    embed_batch = []
    pbar = tqdm(total=len(all_files), desc="Processing", unit="file")

    for file_path in all_files:
        try:
            rel_path = file_path.relative_to(code_dir).as_posix()
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            embed_batch.append({
                "path": rel_path,
                "content": content,
                "language": file_path.suffix.lstrip("."),
                "file_path": file_path  # not stored, just for ref
            })
        except Exception as e:
            print(f"\n⚠️ Skipping {file_path.name}: {e}")

        # Embed when embed_batch is full or last file
        if len(embed_batch) >= embed_batch_size or len(embed_batch) > 0 and file_path == all_files[-1]:
            texts = [item["content"] for item in embed_batch]
            try:
                vectors = ef(texts)
                for item, vec in zip(embed_batch, vectors):
                    write_buffer.append({
                        "path": item["path"],
                        "content": item["content"],
                        "language": item["language"],
                        "vector": vec
                    })
            except Exception as e:
                print(f"\n❌ Embedding failed for batch: {e}")
            embed_batch = []

        pbar.update(1)

        # Write when write_buffer is full
        if len(write_buffer) >= write_batch_size:
            df = pd.DataFrame(write_buffer)
            tbl.add(df)
            total_written += len(write_buffer)
            write_buffer = []
            gc.collect()  # help memory

    # Write remaining
    if write_buffer:
        df = pd.DataFrame(write_buffer)
        tbl.add(df)
        total_written += len(write_buffer)

    pbar.close()
    print(f"\n✅ Indexed {total_written} files into '{db_path}'")

def search_code(db_path: str, query: str, table_name: str = "code", paths_only: bool = False, limit: int = 5, n_lines: int = 16):
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
        if not paths_only:
            print("-" * 60)
            lines = row["content"].splitlines()
            print("\n".join(lines[:n_lines]))
            if len(lines) > n_lines:
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
    srch.add_argument("--paths-only", action="store_true", help="Show only file paths in results")
    srch.add_argument("--n-lines", type=int, default=16, help="Number of lines to show in results")
    srch.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    if args.command == "index":
        index_codebase(args.db, args.code_dir)
    elif args.command == "search":
        search_code(args.db, args.query, paths_only=args.paths_only, limit=args.limit, n_lines=args.n_lines)