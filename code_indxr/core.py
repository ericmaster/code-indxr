import os
import fnmatch
from pathlib import Path
from typing import List, Dict, Any

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".html", ".css", ".scss", ".sql", ".sh", ".bash", ".zsh", ".md"
}

SKIP_PATTERNS = [
    "node_modules", ".git", "__pycache__", "*.pyc", ".venv", "venv",
    ".env", "*.min.js", "*.bundle.js", "dist", "build", "coverage",
    "*.log", "*.tmp", "*.DS_Store", ".mypy_cache", ".pytest_cache"
]

def should_skip(path: Path) -> bool:
    for pattern in SKIP_PATTERNS:
        if fnmatch.fnmatch(path.name, pattern) or pattern in str(path):
            return True
    return False

def read_files(root_dir: Path) -> List[Dict[str, Any]]:
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
                })
            except Exception as e:
                print(f"⚠️ Skipping {file_path}: {e}")
    return chunks