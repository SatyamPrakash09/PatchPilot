from langchain.tools import tool
from pathlib import Path
import subprocess
import json


@tool
def list_dir(dir_path: str = ".") -> dict:
    """List all directories inside a given directory.

    Args:
        dir_path: directory path in which you want to search folders. Defaults to "." (current directory).
    """
    if not dir_path or not str(dir_path).strip():
        dir_path = "."

    resolved_path = Path(dir_path).expanduser().resolve()

    if not resolved_path.exists():
        return {
            "message": f"Directory does not exist: {resolved_path}",
            "status": "error"
        }

    if not resolved_path.is_dir():
        return {
            "message": f"Path is not a directory: {resolved_path}",
            "status": "error"
        }

    folders = [
        str(folder)
        for folder in sorted(resolved_path.iterdir())
        if folder.is_dir()
    ]

    return {
        "folders": folders,
        "count": len(folders),
        "directory": str(resolved_path),
        "status": "success"
    }


@tool
def list_file(dir_path: str = ".") -> dict:
    """List all the files present in the provided dir_path.

    Args:
        dir_path: directory path in which you want to search files. Defaults to "." (current directory).

    Returns:
        dict: files present in the directory
    """
    if not dir_path or not str(dir_path).strip():
        dir_path = "."

    resolved_path = Path(dir_path).expanduser().resolve()
    if not resolved_path.exists():
        return {
            "message": f"Directory does not exist: {resolved_path}",
            "status": "error"
        }
    if not resolved_path.is_dir():
        return {
            "message": f"Path is not a directory: {resolved_path}. If you want to read this file, use read_file_chunk.",
            "status": "error"
        }

    files = [str(file) for file in sorted(resolved_path.iterdir()) if file.is_file()]
    return {
        "files": files,
        "count": len(files),
        "directory": str(resolved_path),
        "status": "success"
    }


@tool
def search_file_type(dir_path: str = ".", file_glob: str = "*") -> dict:
    """Search files of a specific type or glob pattern in the given directory.

    Args:
        dir_path: path of the directory you want to search. Defaults to ".".
        file_glob: glob pattern or extension (e.g. "*.py", "*.json"). Defaults to "*".

    Returns:
        dict: files matching the pattern
    """
    if not dir_path or not str(dir_path).strip():
        dir_path = "."

    resolved_path = Path(dir_path).expanduser().resolve()
    if not resolved_path.exists():
        return {"message": f"Directory does not exist: {resolved_path}", "status": "error"}
    if not resolved_path.is_dir():
        return {"message": f"Path is not a directory: {resolved_path}", "status": "error"}

    file_glob = file_glob.strip() if file_glob else "*"
    if not file_glob:
        file_glob = "*"

    files = [str(f) for f in sorted(resolved_path.glob(file_glob)) if f.is_file()]
    return {
        "directory": str(resolved_path),
        "files": files,
        "glob_type": file_glob,
        "file_count": len(files),
        "status": "success"
    }


MAX_CHUNK = 500


@tool
def read_file_chunk(
    filepath: str,
    start_line: int = 1,
    end_line: int = MAX_CHUNK,
) -> dict:
    """Read a specific line range from a file.

    Lines are 1-indexed and inclusive on both ends.
    If start_line / end_line are omitted the first 500 lines are returned.
    Use this for inspecting source code, configuration, Markdown, JSON,
    YAML, TOML, CSV, and similar text files.

    Args:
        filepath: Path to the file to read.
        start_line: First line to include (1-indexed, default 1).
        end_line: Last line to include (1-indexed, inclusive, default 500).
    """

    if not filepath or not str(filepath).strip():
        return {
            "message": "File path is not provided.",
            "status": "error",
        }

    path = Path(filepath).expanduser().resolve()

    if not path.exists():
        return {
            "message": f"File does not exist: {path}",
            "status": "error",
        }

    if path.is_dir():
        return {
            "message": (
                f"'{path}' is a directory. "
                "Use list_file/list_dir instead."
            ),
            "status": "error",
        }

    if not path.is_file():
        return {
            "message": f"'{path}' is not a regular file.",
            "status": "error",
        }

    # Validate line range.
    if start_line < 1:
        start_line = 1
    if end_line < start_line:
        return {
            "message": (
                f"end_line ({end_line}) must be >= start_line ({start_line})."
            ),
            "status": "error",
        }

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        all_lines = content.splitlines()
        total_lines = len(all_lines)

        # Clamp to actual file length.
        actual_start = min(start_line, total_lines) if total_lines else 1
        actual_end = min(end_line, total_lines) if total_lines else 0

        # Slice (convert 1-indexed inclusive to 0-indexed exclusive).
        selected = all_lines[actual_start - 1 : actual_end]
        chunk = "\n".join(selected)

        has_more = actual_end < total_lines

        if has_more:
            chunk += (
                "\n\n[TRUNCATED]\n"
                f"Showing lines {actual_start}–{actual_end} "
                f"of {total_lines}.\n"
                "Call read_file_chunk with a later range "
                "or use read_symbol to jump to a specific symbol."
            )

        return {
            "filepath": str(path),
            "file_size": path.stat().st_size,
            "total_lines": total_lines,
            "start_line": actual_start,
            "end_line": actual_end,
            "content": chunk,
            "has_more": has_more,
            "status": "success",
        }

    except Exception as e:
        return {
            "message": f"Failed to read file: {e}",
            "status": "error",
        }
