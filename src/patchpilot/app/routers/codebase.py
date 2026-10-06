from typing import Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from patchpilot.tools.codebase_tool import (
    build_codebase,
    search_codebase,
    read_symbol,
    get_codebase_status,
    get_codebase_files,
    search_codebase_structured,
    read_symbol_detail,
    get_runtime,
)

router = APIRouter(prefix="/codebase", tags=["Codebase"])


class CodebaseIndexRequest(BaseModel):
    repo_path: str = Field(default=".", description="Path to repository or directory to index")
    force: bool = Field(default=False, description="Force re-indexing even if already indexed")


class CodebaseSearchRequest(BaseModel):
    query: str = Field(..., description="Function or class name to search for")
    repo_path: str = Field(default=".", description="Repository path")


class CodebaseSymbolRequest(BaseModel):
    file_path: str = Field(..., description="File path containing the symbol")
    symbol_name: str = Field(..., description="Name of the function or class to read")
    repo_path: str = Field(default=".", description="Repository path")


@router.get("/status")
def codebase_status(repo_path: str = Query(default=".", description="Repository path")):
    """Get indexing status, file count, and symbol count for a repository."""
    try:
        status = get_codebase_status(repo_path)
        return {"status": "success", "data": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
@router.post("/build")
def index_codebase(body: CodebaseIndexRequest):
    """Build or rebuild Tree-sitter codebase index for the target repository."""
    try:
        runtime = get_runtime(body.repo_path)
        already_indexed = runtime.index is not None and not body.force
        msg = build_codebase.invoke({"repo_path": body.repo_path, "force": body.force})
        status = runtime.get_status()
        return {
            "status": "success",
            "already_indexed": already_indexed,
            "message": msg,
            "data": status,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
def search_codebase_endpoint(body: CodebaseSearchRequest):
    """Search functions, classes, and definitions across the indexed codebase."""
    try:
        matches = search_codebase_structured(body.query, body.repo_path)
        raw = search_codebase.invoke({"repo_path": body.repo_path, "query": body.query})
        return {
            "status": "success",
            "query": body.query,
            "count": len(matches),
            "matches": matches,
            "raw_output": raw,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/symbol")
def read_symbol_endpoint(body: CodebaseSymbolRequest):
    """Read the complete source code and line bounds of a specific symbol."""
    try:
        detail = read_symbol_detail(body.file_path, body.symbol_name, body.repo_path)
        if not detail.get("found"):
            raise HTTPException(status_code=404, detail=detail.get("error", "Symbol not found"))
        return {
            "status": "success",
            "data": detail,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
def list_indexed_files(repo_path: str = Query(default=".", description="Repository path")):
    """Get list of all indexed files and their discovered symbol outlines."""
    try:
        files = get_codebase_files(repo_path)
        return {
            "status": "success",
            "repo_path": repo_path,
            "count": len(files),
            "files": files,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
