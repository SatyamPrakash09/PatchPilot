from patchpilot.codebase.parser import parse_python_file
from patchpilot.codebase.symbols import *
from pathlib import Path

tree, source = parse_python_file(Path("/home/onix/Code/Orbit/backend/src/models/user_model.py"))
# print(tree.root_node, source,"\n")

tree, source = parse_python_file(Path("/home/onix/Code/Orbit/backend/src/models/user_model.py"))

symbols = extract_symbols(tree.root_node, source)

for symbol in symbols:
    print(symbol)
    
    
from patchpilot.codebase.index import CodebaseIndex


index = CodebaseIndex(".")

index.build()

for file in index.files:

    print(f"\n{file.path}")

    for symbol in file.symbols:
        print(
            f"  {symbol.kind}: "
            f"{symbol.name} "
            f"({symbol.start_line}-{symbol.end_line})"
        )