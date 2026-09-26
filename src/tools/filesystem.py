from langchain.tools import tool
from pathlib import Path


@tool
def list_file(dir_path) -> dict:
    """List all the files present in the provided dir_path

    Args:
        dir_path (str): directory path in which you want to seach files

    Returns:
        dict: files present in the directory
        
    """
    dir_path = Path(dir_path).resolve()
    
    files = [file for file in dir_path.iterdir() if file.is_file()]
    return {"files":files}

# print(list_file.invoke("."))


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
        return {"files":list_file.invoke(str(dir_path)), "glob_type": file_glob}
    
    dir_path = Path(dir_path).resolve()
    files =  [str(file) for file in dir_path.glob(file_glob) if file.is_file()]
    return {"directory":str(dir_path),"files":files, "glob_type": file_glob, "file_count": len(files)}

print(search_file_type.invoke({
    "dir_path": "/home/onix/Downloads",
    "file_glob": "*.png"
}))
