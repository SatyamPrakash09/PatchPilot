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


@tool
def read_file(file_path: str, max_lines: int = 500) -> dict:
    """Reads the content and metadata of a specified file based on its extension.

    Supports reading plaintext files (.py, .txt, .md, .toml, .yaml, etc.), 
    structured data (.json), and tabular data (.csv).

    Args:
        file_path: The filesystem path of the file to be read.
        max_lines: Maximum number of lines to return for large files (default: 500).

    Returns:
        A dictionary containing file_content, file_size, and status.
    """
    if not file_path or not str(file_path).strip():
        return {"message": "File path is not provided", "status": "error"}

    path_obj = Path(file_path).expanduser().resolve()
    if not path_obj.exists():
        return {"message": f"File does not exist: {path_obj}", "status": "error"}
    if path_obj.is_dir():
        return {
            "message": f"The path '{path_obj}' is a directory, not a file. Use list_file or list_dir instead.",
            "status": "error"
        }
    if not path_obj.is_file():
        return {"message": f"The path '{path_obj}' is not a valid regular file.", "status": "error"}

    ext = path_obj.suffix.lower().lstrip(".")

    try:
        if ext == "json":
            with open(path_obj, "r", encoding="utf-8", errors="replace") as file:
                file_content = json.load(file)
        elif ext == "csv":
            import pandas as pd
            df = pd.read_csv(path_obj, nrows=max_lines)
            file_content = df.to_dict(orient="records")
        else:
            with open(path_obj, "r", encoding="utf-8", errors="replace") as file:
                lines = file.readlines()
                if len(lines) > max_lines:
                    file_content = "".join(lines[:max_lines]) + f"\n... [Truncated: showing {max_lines}/{len(lines)} lines]"
                else:
                    file_content = "".join(lines)
    except Exception as e:
        return {"message": f"Failed to read file: {str(e)}", "status": "error"}

    return {
        "file_path": str(path_obj),
        "file_size": path_obj.stat().st_size,
        "file_content": file_content,
        "status": "success"
    }

