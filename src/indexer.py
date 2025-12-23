import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import fnmatch
import openai
from dotenv import load_dotenv
import lancedb
from .embedder import get_embedding_function

# Common code file extensions
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".html", ".css", ".scss", ".sh", ".bash", ".zsh"
}

# Files/folders to skip
SKIP_PATTERNS = [
    "node_modules", ".git", "__pycache__", "*.pyc", ".venv", "venv",
    ".env", "*.min.js", "*.bundle.js", "dist", "build", "coverage",
    "*.log", "*.tmp", "*.DS_Store"
]

def should_skip(path: Path) -> bool:
    """Check if a file or folder should be skipped."""
    for pattern in SKIP_PATTERNS:
        if fnmatch.fnmatch(path.name, pattern) or pattern in str(path):
            return True
    return False

def read_files(root_dir: Path) -> List[Dict[str, Any]]:
    """Recursively read code files and return chunks (one per file for simplicity)."""
    chunks = []
    for file_path in root_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in CODE_EXTENSIONS and not should_skip(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                rel_path = file_path.relative_to(root_dir).as_posix()
                chunks.append({
                    "path": rel_path,
                    "content": content,
                    "language": file_path.suffix.lstrip("."),
                    "type": "file"
                })
            except Exception as e:
                print(f"⚠️ Skipping {file_path}: {e}", file=sys.stderr)
    return chunks

def index_codebase(db_path: str, code_dir: str, table_name: str = "code"):
    """Index a code directory into LanceDB."""
    db = lancedb.connect(db_path)
    chunks = read_files(Path(code_dir))

    if not chunks:
        print("⚠️ No code files found. Check directory and permissions.")
        return

    # Create LanceDB table with embedding function
    try:
        ef = get_embedding_function()

        tbl = db.create_table(
            table_name,
            data=chunks,
            # embedding_function=ef,
            embedding_functions={"content": ef},
            mode="overwrite"
        )
        print(f"✅ Indexed {len(chunks)} files into table '{table_name}' at {db_path}")
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        raise

def search_code(db_path: str, query: str, table_name: str = "code", limit: int = 5):
    """Search indexed codebase using natural language."""
    db = lancedb.connect(db_path)
    tbl = db.open_table(table_name)
    results = tbl.search(query).limit(limit).to_pandas()
    return results[["path", "content", "_distance"]]
