import subprocess
from pathlib import Path
from langchain.tools import tool

def find_git_repos(path: str) -> list[Path]:
    """Find Git repositories at, above, or below the given path."""

    root = Path(path or ".").expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")

    if root.is_file():
        root = root.parent

    # 1. Check if the path itself or any parent is a Git repository
    current = root
    while True:
        if (current / ".git").exists():
            return [current]
        if current == current.parent:
            break
        current = current.parent

    # 2. Check immediate subdirectories (skipping common heavy folders)
    repos = []
    ignored = {".venv", "venv", "node_modules", ".cache", "__pycache__"}
    try:
        for child in root.iterdir():
            if child.name in ignored:
                continue
            if (child / ".git").exists():
                repos.append(child)
    except (PermissionError, OSError):
        pass

    return sorted(set(repos))


def run_git(workspace_path: str, args: list[str]) -> str:
    """Run a Git command in the appropriate repository."""

    try:
        workspace = workspace_path if workspace_path and workspace_path.strip() else "."
        repos = find_git_repos(workspace)

        if not repos:
            return (
                f"No Git repository found at, above, or below: "
                f"{Path(workspace).resolve()}"
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
def git_status(workspace: str = ".") -> str:
    """Return the current Git working tree status and active branch.

    Shows staged, unstaged, and untracked files along with the current
    branch information.

    Args:
        workspace: Path to the Git repository or directory inside it. Defaults to current directory (".").

    Returns:
        A string containing the Git status output.
    """
    return run_git(
        workspace,
        ["status", "--short", "--branch"]
    )

@tool
def git_diff(
    workspace: str = ".",
    max_chars: int = 20_000,
) -> str:
    """Return a bounded Git diff."""

    output = run_git(
        workspace,
        ["diff", "--no-ext-diff"],
    )

    if len(output) <= max_chars:
        return output

    return (
        output[:max_chars]
        + "\n\n[DIFF TRUNCATED]\n"
        f"Original size: {len(output):,} characters"
    )

@tool
def git_diff_file(
    file_path: str,
    workspace: str = ".",
    max_chars: int = 20_000,
) -> str:
    """Show the diff for a specific file."""

    output = run_git(
        workspace,
        ["diff", "--", file_path],
    )

    if len(output) > max_chars:
        output = (
            output[:max_chars]
            + "\n\n[DIFF TRUNCATED]"
        )

    return output

@tool
def git_branch(workspace: str = ".") -> str:
    """Return the name of the currently active Git branch.

    Args:
        workspace: Path to the Git repository or directory inside it. Defaults to current directory (".").

    Returns:
        The name of the current branch as a string.
    """
    return run_git(
        workspace,
        ["branch", "--show-current"]
    )


@tool
def git_logs(workspace: str = ".") -> str:
    """Return the latest 10 Git commits with branch and tag information.

    Each commit is displayed in a compact one-line format.

    Args:
        workspace: Path to the Git repository or directory inside it. Defaults to current directory (".").

    Returns:
        A string containing the latest 10 commits.
    """
    return run_git(
        workspace,
        ["log", "--oneline", "--decorate", "-10"]
    )


@tool
def git_remote_branch(workspace: str = ".") -> str:
    """Return the configured Git remote repositories and their URLs.

    This shows the fetch and push URLs configured for each Git remote.

    Args:
        workspace: Path to the Git repository or directory inside it. Defaults to current directory (".").

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