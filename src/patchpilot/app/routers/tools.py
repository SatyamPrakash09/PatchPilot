from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from patchpilot.tools.git import (
    git_status,
    git_diff,
    git_diff_file,
    git_branch,
    git_logs,
    git_remote_branch,
)
from patchpilot.tools.filesystem import (
    list_dir,
    list_file,
    search_file_type,
    read_file_chunk,
)
from patchpilot.tools.search import search_code

router = APIRouter(prefix="/tools", tags=["Tools"])


# Git Models
class GitWorkspaceRequest(BaseModel):
    workspace: str = Field(default=".", description="Path to Git repository or directory inside it")


class GitDiffRequest(BaseModel):
    workspace: str = Field(default=".", description="Path to Git repository")
    file_path: str | None = Field(default=None, description="Optional specific file path for diff")
    max_chars: int = Field(default=20000, description="Maximum characters of diff to return")


# FS Models
class DirectoryRequest(BaseModel):
    dir_path: str = Field(default=".", description="Directory path")


class SearchFileTypeRequest(BaseModel):
    dir_path: str = Field(default=".", description="Directory path")
    file_glob: str = Field(default="*", description="Glob pattern or file extension")


class ReadFileChunkRequest(BaseModel):
    filepath: str = Field(..., description="Path to file to read")
    start_line: int = Field(default=1, description="Starting line (1-indexed)")
    end_line: int = Field(default=500, description="Ending line (1-indexed, inclusive)")


# Search Models
class SearchCodeRequest(BaseModel):
    query: str = Field(..., description="String or regex pattern to search for with ripgrep")
    path: str = Field(default=".", description="File or directory path to search within")


# Git Endpoints
@router.post("/git/status")
def get_git_status(body: GitWorkspaceRequest):
    """Get Git status and current branch for the workspace."""
    try:
        res = git_status.invoke({"workspace": body.workspace})
        return {"status": "success", "workspace": body.workspace, "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/git/diff")
def get_git_diff(body: GitDiffRequest):
    """Get Git diff for working tree or specific file."""
    try:
        if body.file_path:
            res = git_diff_file.invoke({
                "file_path": body.file_path,
                "workspace": body.workspace,
                "max_chars": body.max_chars,
            })
        else:
            res = git_diff.invoke({
                "workspace": body.workspace,
                "max_chars": body.max_chars,
            })
        return {"status": "success", "workspace": body.workspace, "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/git/branch")
def get_git_branch(body: GitWorkspaceRequest):
    """Get active Git branch name."""
    try:
        res = git_branch.invoke({"workspace": body.workspace})
        return {"status": "success", "branch": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/git/logs")
def get_git_logs(body: GitWorkspaceRequest):
    """Get recent Git commit logs."""
    try:
        res = git_logs.invoke({"workspace": body.workspace})
        return {"status": "success", "logs": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/git/remotes")
def get_git_remotes(body: GitWorkspaceRequest):
    """Get configured Git remotes."""
    try:
        res = git_remote_branch.invoke({"workspace": body.workspace})
        return {"status": "success", "remotes": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Filesystem Endpoints
@router.post("/fs/list-dirs")
def get_list_dirs(body: DirectoryRequest):
    """List subdirectories in a given directory."""
    try:
        return list_dir.invoke({"dir_path": body.dir_path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fs/list-files")
def get_list_files(body: DirectoryRequest):
    """List files in a given directory."""
    try:
        return list_file.invoke({"dir_path": body.dir_path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fs/search-file-type")
def get_search_file_type(body: SearchFileTypeRequest):
    """Search files matching a glob pattern."""
    try:
        return search_file_type.invoke({"dir_path": body.dir_path, "file_glob": body.file_glob})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fs/read-chunk")
def get_read_chunk(body: ReadFileChunkRequest):
    """Read line chunk from a specific file."""
    try:
        return read_file_chunk.invoke({
            "filepath": body.filepath,
            "start_line": body.start_line,
            "end_line": body.end_line,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Search Endpoints
@router.post("/search/code")
def get_search_code(body: SearchCodeRequest):
    """Search for text pattern in files using ripgrep."""
    try:
        return search_code.invoke({"query": body.query, "path": body.path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
