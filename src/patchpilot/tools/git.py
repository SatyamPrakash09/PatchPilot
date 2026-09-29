import subprocess
from pathlib import Path
from langchain.tools import tool

def find_git_repos(path: str) -> list[Path]:
    """Find Git repositories at or below the given path."""

    root = Path(path).expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")

    if root.is_file():
        root = root.parent

    repos = []

    # The path itself is a repository.
    if (root / ".git").exists():
        return [root]

    # Search child directories.
    for git_dir in root.rglob(".git"):
        repo = git_dir.parent

        if git_dir.is_dir() or git_dir.is_file():
            repos.append((repo))

    return sorted(set(repos))

# print(find_git_repos("/home/onix/Code/Orbit"))

def run_git(workspace_path: str, args: list[str]) -> str:
    """Run a Git command in the appropriate repository."""

    try:
        repos = find_git_repos(workspace_path)

        if not repos:
            return (
                f"No Git repository found at or below: "
                f"{Path(workspace_path).resolve()}"
            )

        if len(repos) > 1:
            return (
                "Multiple Git repositories found:\n"
                + "\n".join(f"- {repo}" for repo in repos)
                + "\nPlease specify which repository to use."
            )

        git_root = repos[0]

        result = subprocess.run(
            ["git", *args],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return (
                f"Git command failed.\n"
                f"Repository: {git_root}\n"
                f"Command: git {' '.join(args)}\n"
                f"Error: {result.stderr.strip()}"
            )

        return result.stdout.strip()

    except FileNotFoundError as e:
        return f"Error: {e}"

    except ValueError as e:
        return f"Error: {e}"

    except subprocess.TimeoutExpired:
        return "Error: Git command timed out."

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
#         "workspace": "/home/onix/Code/Orbit/backend"
#     })
# })