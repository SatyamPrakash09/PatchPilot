from langchain.tools import tool
import subprocess
import json 
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