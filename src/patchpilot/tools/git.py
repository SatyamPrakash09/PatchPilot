import subprocess
from pathlib import Path
from langchain.tools import tool

def run_git(workspace_path:str, args:list[str]) -> str:
    result =  subprocess.run(
        ["git", *args],
        cwd=workspace_path,
        capture_output=True,
        text=True    
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


@tool
def git_status(workspace: str) -> str:
    """Return the current Git working tree status and active branch.

    Shows staged, unstaged, and untracked files along with the current
    branch information.

    Args:
        workspace: Absolute path to the Git repository.

    Returns:
        A string containing the Git status output.
    """
    return run_git(
        workspace,
        ["status", "--short", "--branch"]
    )


@tool
def git_diff(workspace: str) -> str:
    """Return the current unstaged changes in the Git repository.

    Displays line-by-line differences between the working tree and the
    index.

    Args:
        workspace: Absolute path to the Git repository.

    Returns:
        A string containing the Git diff output.
    """
    return run_git(
        workspace,
        ["diff"]
    )


@tool
def git_branch(workspace: str) -> str:
    """Return the name of the currently active Git branch.

    Args:
        workspace: Absolute path to the Git repository.

    Returns:
        The name of the current branch as a string.
    """
    return run_git(
        workspace,
        ["branch", "--show-current"]
    )


@tool
def git_logs(workspace: str) -> str:
    """Return the latest 10 Git commits with branch and tag information.

    Each commit is displayed in a compact one-line format.

    Args:
        workspace: Absolute path to the Git repository.

    Returns:
        A string containing the latest 10 commits.
    """
    return run_git(
        workspace,
        ["log", "--oneline", "--decorate", "-10"]
    )


@tool
def git_remote_branch(workspace: str) -> str:
    """Return the configured Git remote repositories and their URLs.

    This shows the fetch and push URLs configured for each Git remote.

    Args:
        workspace: Absolute path to the Git repository.

    Returns:
        A string containing the configured Git remote information.
    """
    return run_git(
        workspace,
        ["remote", "-v"]
    )


# print({
#     "message": git_remote_branch.invoke({
#         "workspace": "/home/onix/Code/PatchPilot"
#     })
# })