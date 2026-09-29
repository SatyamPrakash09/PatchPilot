from pathlib import Path

from langchain_core.tools import tool

from patchpilot.codebase.index import CodebaseIndex


class CodebaseRuntime:

    def __init__(self, repo_path: str | Path):
        self.repo_path = (
            Path(repo_path)
            .expanduser()
            .resolve()
        )

        self.index: CodebaseIndex | None = None

    def build(self) -> None:

        if self.index is not None:
            return

        self.index = CodebaseIndex(
            self.repo_path
        )

        self.index.build()


runtime: CodebaseRuntime | None = None


def initialize_codebase_runtime(
    repo_path: str | Path,
) -> None:
    global runtime
    runtime = CodebaseRuntime(repo_path)


def get_runtime(repo_path: str | Path | None = None) -> CodebaseRuntime:
    global runtime

    target_path = Path(repo_path or ".").expanduser().resolve()
    if runtime is None:
        runtime = CodebaseRuntime(target_path)
    elif repo_path is not None and runtime.repo_path != target_path:
        runtime = CodebaseRuntime(target_path)

    return runtime


@tool
def build_codebase(repo_path: str = ".") -> str:
    """Build the Tree-sitter codebase index for the specified repository or current directory.

    Call this when you need to understand the structure
    of the repository or search for functions and classes.
    
    Args:
        repo_path: The directory or repository path to index. Defaults to current directory (".").
    """
    try:
        runtime = get_runtime(repo_path)

        if runtime.index is not None:
            return f"Codebase at '{runtime.repo_path}' is already indexed ({len(runtime.index.files)} files)."

        runtime.build()

        return (
            f"Codebase indexed successfully.\n"
            f"Repository: {runtime.repo_path}\n"
            f"Files indexed: {len(runtime.index.files)}"
        )
    except Exception as e:
        return f"Error indexing codebase: {str(e)}"


@tool
def search_codebase(query: str, repo_path: str = ".") -> str:
    """Search the codebase for functions and classes.

    Use this to locate relevant source code before reading
    the implementation.
    
    Args:
        query: The symbol or function/class name to search for.
        repo_path: The directory or repository path. Defaults to current directory (".").
    """
    try:
        runtime = get_runtime(repo_path)

        if runtime.index is None:
            runtime.build()

        results = runtime.index.search_symbols(query)

        if not results:
            return f"No matching symbols found for '{query}' in {runtime.repo_path}."

        output = []
        for file, symbol in results:
            output.append(
                f"{file.path}:"
                f"{symbol.start_line}-"
                f"{symbol.end_line} "
                f"{symbol.kind} "
                f"{symbol.name}"
            )

        return "\n".join(output)
    except Exception as e:
        return f"Error searching codebase: {str(e)}"


@tool
def read_symbol(
    file_path: str,
    symbol_name: str,
    repo_path: str = ".",
) -> str:
    """Read the complete source code of a specific symbol.
    
    Args:
        file_path: Relative or absolute path of the file containing the symbol.
        symbol_name: The name of the function or class to extract.
        repo_path: The repository path. Defaults to current directory (".").
    """
    try:
        runtime = get_runtime(repo_path)

        if runtime.index is None:
            runtime.build()

        file = runtime.index.get_file(file_path)

        # Fallback: check if relative to repo_path
        if file is None:
            try:
                rel = str(Path(file_path).resolve().relative_to(runtime.repo_path))
                file = runtime.index.get_file(rel)
            except ValueError:
                pass

        if file is None:
            return f"File not found in index: {file_path}"

        for symbol in file.symbols:
            if symbol.name == symbol_name:
                source = runtime.index.get_symbol_source(
                    file,
                    symbol,
                )
                return (
                    f"# {file.path}:"
                    f"{symbol.start_line}-"
                    f"{symbol.end_line}\n\n"
                    f"{source}"
                )

        return (
            f"Symbol '{symbol_name}' "
            f"not found in {file_path}"
        )
    except Exception as e:
        return f"Error reading symbol: {str(e)}"