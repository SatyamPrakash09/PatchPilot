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
            "message": f"Path is not a directory: {resolved_path}. If you want to read this file, use read_file.",
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


MAX_CHARS = 30_000
DEFAULT_MAX_LINES = 300


@tool
def read_file(
    file_path: str,
    max_lines: int = DEFAULT_MAX_LINES,
    max_chars: int = MAX_CHARS,
) -> dict:
    """Read a bounded portion of a file.

    Use this for inspecting files such as Python source, configuration,
    Markdown, JSON, YAML, TOML, and CSV.

    Output is bounded by both max_lines and max_chars to prevent
    excessive context usage.
    """

    if not file_path or not str(file_path).strip():
        return {
            "message": "File path is not provided",
            "status": "error",
        }

    path = Path(file_path).expanduser().resolve()

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

    try:
        # Read text once.
        content = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        lines = content.splitlines()

        original_lines = len(lines)
        original_chars = len(content)

        # First limit lines.
        selected_lines = lines[:max_lines]

        content = "\n".join(selected_lines)

        truncated_by_lines = original_lines > max_lines

        # Then enforce hard character limit.
        truncated_by_chars = len(content) > max_chars

        if truncated_by_chars:
            content = content[:max_chars]

        truncated = (
            truncated_by_lines
            or truncated_by_chars
        )

        if truncated:
            content += (
                "\n\n"
                "[TRUNCATED]\n"
                f"Showing at most {max_lines:,} lines "
                f"and {max_chars:,} characters.\n"
                f"Original: {original_lines:,} lines, "
                f"{original_chars:,} characters.\n"
                "Use a more specific range or read_symbol "
                "to inspect the required code."
            )

        return {
            "file_path": str(path),
            "file_size": path.stat().st_size,
            "lines": original_lines,
            "characters": original_chars,
            "file_content": content,
            "truncated": truncated,
            "status": "success",
        }

    except Exception as e:
        return {
            "message": f"Failed to read file: {e}",
            "status": "error",
        }
