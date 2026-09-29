from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from pathlib import Path

py_language = Language(tspython.language())


def parse_python_file(path:str)->str:
    path = Path(path).resolve()
    source = path.read_bytes()
    parser = Parser(py_language)
    tree = parser.parse(source)
    return tree, source



