from dataclasses import dataclass, field
from pathlib import Path

from patchpilot.codebase.parser import parse_python_file
from patchpilot.codebase.symbols import Symbol, extract_symbols

supported_extensions={
    ".py":"python"
}

@dataclass
class FileIndex:
    path:str
    language:str
    symbols: list[Symbol] = field(default_factory=list)
    

class CodebaseIndex:
    def __init__(self, root:str | Path):
        self.root = Path(root).expanduser().resolve()
        self.files : list[FileIndex] = []
    
    def build(self) ->None:
        self.files.clear()
        
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in supported_extensions:
                continue
            
            if any(
                part in {
                    ".git",
                    ".venv",
                    ".env",
                    "venv",
                    "node_modules",
                    "__pychache__"
                }
                for part in path.parts
            ):
                continue
            
            language = supported_extensions[path.suffix]
            
            if language == "python":
                tree, source = parse_python_file(path)
                
                symbols = extract_symbols(tree.root_node, source)
                
                relative_path = str(path.relative_to(self.root))
                
                self.files.append(
                    FileIndex(
                        path=relative_path,
                        language=language,
                        symbols=symbols
                    )
                )
                
    def search_symbol(self, query:str)->list[tuple[FileIndex, Symbol]]:
        query = query.lower()
        
        results = []
        
        for file in self.files:
            for symbol in file.symbols:
                
                if query in symbol.name.lower():
                    results.append( 
                        (file, symbol)
                    )
                    
        return results
    
    def get_symbol_source(
        self, 
        file:FileIndex,
        symbol:Symbol
    )->str:
        path = self.root/file.path
        source = path.read_bytes()
        
        return source[
            symbol.start_byte:symbol.end_byte
        ].decode("utf-8")
        
    def get_file(self, path:str)->FileIndex |None:
        for file in self.files:
            if file.path == path:
                return file
        return None