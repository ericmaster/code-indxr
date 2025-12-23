"""
MCP-compliant Server for Code Indexer
-------------------------------------
Implements /v1/context, /v1/search, and /v1/manifest endpoints per MCP spec.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os
import shutil
from . import cli

app = FastAPI(title="Code Indexer MCP Server (MCP Spec)")

# MCP Context ingestion: POST /v1/context
class MCPFile(BaseModel):
    path: str
    content: str
    language: Optional[str] = None

class ContextRequest(BaseModel):
    files: List[MCPFile]
    db_path: str

@app.post("/v1/context")
def ingest_context(req: ContextRequest):
    # Write files to a temp dir, then index
    with tempfile.TemporaryDirectory() as tmpdir:
        for f in req.files:
            file_path = os.path.join(tmpdir, f.path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as out:
                out.write(f.content)
        cli.index_codebase(req.db_path, tmpdir)
    return {"status": "ok", "db": req.db_path}

# MCP Search: POST /v1/search
class SearchRequest(BaseModel):
    query: str
    db_path: str
    limit: Optional[int] = 5
    n_lines: Optional[int] = 16
    paths_only: Optional[bool] = False

class SearchResult(BaseModel):
    path: str
    content: Optional[str] = None
    score: Optional[float] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]

@app.post("/v1/search", response_model=SearchResponse)
def mcp_search(req: SearchRequest):
    from code_indxr import cli
    ef = cli.get_embedding_function()
    query_vec = ef([req.query])[0]
    import lancedb
    db = lancedb.connect(req.db_path)
    tbl = db.open_table("code")
    results = tbl.search(query_vec).limit(req.limit).to_pandas()
    out = []
    for _, row in results.iterrows():
        out.append(SearchResult(
            path=row["path"],
            content=(row["content"] if not req.paths_only else None),
            score=(1.0 - row["_distance"]) if "_distance" in row else None
        ))
    return SearchResponse(results=out)

# MCP Manifest: GET /v1/manifest
@app.get("/v1/manifest")
def manifest():
    return {
        "name": "Code Indexer MCP Server",
        "version": "1.0",
        "capabilities": ["context", "search"],
        "description": "Semantic code search and indexing via MCP API"
    }

# To run: uvicorn code_indxr.mcp_server:app --reload
