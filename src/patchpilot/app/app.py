from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from patchpilot.app.routers.agent import router as agent_router
from patchpilot.app.routers.codebase import router as codebase_router
from patchpilot.app.routers.tools import router as tools_router
from patchpilot.tools.codebase_tool import build_codebase, search_codebase, read_symbol_detail

app = FastAPI(
    title="PatchPilot Web API",
    description="Web API for PatchPilot - AI codebase investigation, Tree-sitter indexing, Git, and developer tools.",
    version="1.0.0",
)

# Enable CORS for web frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount feature routers under both /api and direct root for maximum client compatibility
app.include_router(agent_router, prefix="/api")
app.include_router(codebase_router, prefix="/api")
app.include_router(tools_router, prefix="/api")

app.include_router(agent_router)
app.include_router(codebase_router)
app.include_router(tools_router)


# Request models for legacy endpoints
class CodeBaseRequest(BaseModel):
    repo_path: str = Field(default=".", description="Path to repository")
    force: bool = Field(default=False, description="Force re-indexing")


class SearchCodeBaseRequest(BaseModel):
    repo_path: str = Field(default=".", description="Path to repository")
    query: str = Field(..., description="Symbol or function name to search for")


class ReadSymbolRequest(BaseModel):
    file_path: str = Field(..., description="Path to file")
    symbol_name: str = Field(..., description="Symbol name")
    repo_path: str = Field(default=".", description="Path to repository")


@app.get("/")
def greet():
    """Welcome and endpoints directory."""
    return {
        "message": "Welcome to PatchPilot Web API",
        "version": "1.0.0",
        "status": "OK",
        "docs_url": "/docs",
        "endpoints": {
            "agent": {
                "run": "POST /api/agent/run",
                "stream": "POST /api/agent/stream (SSE)",
                "info": "GET /api/agent/info",
            },
            "codebase": {
                "status": "GET /api/codebase/status?repo_path=.",
                "index": "POST /api/codebase/index",
                "search": "POST /api/codebase/search",
                "symbol": "POST /api/codebase/symbol",
                "files": "GET /api/codebase/files?repo_path=.",
            },
            "tools": {
                "git_status": "POST /api/tools/git/status",
                "git_diff": "POST /api/tools/git/diff",
                "git_branch": "POST /api/tools/git/branch",
                "git_logs": "POST /api/tools/git/logs",
                "git_remotes": "POST /api/tools/git/remotes",
                "fs_list_dirs": "POST /api/tools/fs/list-dirs",
                "fs_list_files": "POST /api/tools/fs/list-files",
                "fs_read_chunk": "POST /api/tools/fs/read-chunk",
                "fs_search_file_type": "POST /api/tools/fs/search-file-type",
                "search_code": "POST /api/tools/search/code",
            },
            "legacy": {
                "structure": "POST /structure",
                "search": "POST /search",
                "symbol": "POST /symbol",
            },
        },
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "patchpilot"}


# Legacy endpoints maintained for backward compatibility
@app.post("/structure")
def build_structure(body: CodeBaseRequest):
    return build_codebase.invoke({"repo_path": body.repo_path, "force": body.force})


@app.post("/search")
def search_structure(body: SearchCodeBaseRequest):
    return search_codebase.invoke({"repo_path": body.repo_path, "query": body.query})


@app.post("/symbol")
def get_symbol(body: ReadSymbolRequest):
    return read_symbol_detail(body.file_path, body.symbol_name, body.repo_path)
