from langchain.tools import tool
from pathlib import Path
import subprocess
import json


@tool
def list_dir(dir_path: str) -> dict:
    """List all directories inside a given directory."""

    if not dir_path or not dir_path.strip():
        return {
            "message": "Directory path is not provided",
            "status": "error"
        }

    dir_path = Path(dir_path).resolve()

    if not dir_path.exists():
        return {
            "message": f"Directory does not exist: {dir_path}",
            "status": "error"
        }

    if not dir_path.is_dir():
        return {
            "message": f"Path is not a directory: {dir_path}",
            "status": "error"
        }

    folders = [
        str(folder)
        for folder in dir_path.iterdir()
        if folder.is_dir()
    ]

    return {
        "folders": folders,
        "count": len(folders),
        "directory": str(dir_path),
        "status": "success"
    }
# print(list_dir.invoke({
#     "dir_path": "/home/onix/Code"
# }))

@tool
def list_file(dir_path) -> dict:
    """List all the files present in the provided dir_path

    Args:
        dir_path (str): directory path in which you want to seach files

    Returns:
        dict: files present in the directory
        
    """
    if(not dir_path.strip()):
            return {"message":"directory path is not provided", "status":"error"}
    
    dir_path = Path((dir_path)).resolve()
    if not dir_path.exists():
        return {
            "message": f"Directory does not exist: {dir_path}",
            "status": "error"
        }
    
    files = [str(file) for file in dir_path.iterdir() if file.is_file()]
    return {"files":files, "count":len(files),"directory":str(dir_path)}

# print(list_file.invoke({"dir_path":"/home/onix/Downloads"}))


@tool
def search_file_type(dir_path:str, file_glob:str) -> dict:
    """search file of specific type in the given directory

    Args:
        dir_path (str): path of the directory you want to search
        file_glob (str): glob value or extension of the file type you want to search. e.g:"*.txt, *.md"

    Returns:
        dict: return file with the required file type
    """
    file_glob = file_glob.strip()
    
    if(not dir_path):
        return {"message":"directory path is not provided", "status":"error"}
    if(not file_glob):
        return list_file.invoke({"dir_path":str(dir_path)})
    
    dir_path = Path(dir_path).resolve()
    files =  [str(file) for file in dir_path.glob(file_glob) if file.is_file()]
    return {"directory":str(dir_path),"files":files, "glob_type": file_glob, "file_count": len(files)}

# print(search_file_type.invoke({
#     "dir_path": "/home/onix/Downloads",
#     "file_glob": "*.png"
# }))

@tool
def read_file(file_path: str) -> dict:
    """Reads the content and metadata of a specified file based on its extension.

    Supports reading plaintext files (.txt, .md), structured data (.json), 
    and tabular data (.csv). Automatically handles missing inputs or invalid paths.

    Args:
        file_path: The filesystem path of the file to be read.

    Returns:
        A dictionary indicating either a success structure or an error message.
        
        On Success:
        {
            "file_path": str,
            "file_size": int,        # Size of the file in bytes
            "file_content": Any      # list/dict for json, dict for csv, str for text
        }
        
        On Failure:
        {
            "message": str,
            "status": "error"
        }
    """
    if not file_path:
        return {"message": "file path is not provided", "status": "error"}
        
    path_obj = Path(file_path)
    if not path_obj.is_file():
        return {"message": "The path is not a valid file path", "status": "error"}
        
    # Extract extension safely and convert to lowercase
    ext = path_obj.suffix.lower().lstrip(".")
    
    try:
        if ext in ["txt", "md"]:
            with open(path_obj, "r", encoding="utf-8") as file:
                file_content = file.read()
                
        elif ext == "json":
            with open(path_obj, "r", encoding="utf-8") as file:
                file_content = json.load(file)
                
        elif ext == "csv":
            import pandas as pd
            # Convert DataFrame to a standard Python dictionary format to ensure JSON safety
            df = pd.read_csv(path_obj)
            file_content = df.to_dict(orient="records")
            
        else:
            # Fallback for other files (read as plain text)
            with open(path_obj, "r", encoding="utf-8") as file:
                file_content = file.read()
                
    except Exception as e:
        return {"message": f"Failed to read file: {str(e)}", "status": "error"}
    
    return {
        "file_path": str(path_obj),  
        "file_size": path_obj.stat().st_size, 
        "file_content": file_content
    }

# print(read_file.invoke({"file_path":"/home/onix/Code/PatchPilot/file.txt"}))

@tool
def search_code(query: str, path: str = ".") -> dict:
    """Searches for a text pattern in a directory using ripgrep.

    This function executes the native `rg` command-line utility with the `--json`
    flag, parses its newline-delimited JSON stream output, and handles common
    process exit codes gracefully without raising process errors.

    Args:
        query: The string or regex pattern to search for.
        path: The file or directory path to search within. Defaults to ".".

    Returns:
        A dictionary containing the execution outcome. The dictionary format 
        varies by status:

        On success (matches found):
            {
                "status": "success",
                "message": str,
                "matches": list[dict]  # Raw JSON objects returned by ripgrep
            }
        On success (no matches found):
            {
                "status": "success",
                "message": "No matches found",
                "matches": []
            }
        On error (invalid path, missing binary, syntax error):
            {
                "status": "error",
                "message": str
            }

    Raises:
        FileNotFoundError: If the `rg` binary is not installed or missing from PATH.
    """

    try:
        if not query.strip():
            return {"message":"Query Parammeter not provided", "status":"error"}
        result = subprocess.run(
            ["rg", query, path, "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        stdout_data = result.stdout
    except subprocess.CalledProcessError as e :
        if e.returncode == 1:
            return {"message":f"No matches found ", "status":"success", "matches":[]}
        return {"message":f"Ripgrep failed: {e.stderr.strip()}", "status":"error"}
    parsed_matches=[]
    for line in stdout_data.strip().split("\n"):
        if line.strip():
            data = json.loads(line)
            if data.get("type") == "match":
                parsed_matches.append(data)
    return {
        "status":"success",
        "message":f"Found {len(parsed_matches)} match records",
        "matches":parsed_matches
    }
# print(search_code.invoke({"query":'open'}))