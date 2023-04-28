import os 
import asyncio
from collections.abc import Iterator
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import PythonLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders.image import UnstructuredImageLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter, PythonCodeTextSplitter
from langchain.document_loaders.base import BaseLoader

# def get_loaders(path):
#     loaders = []
#     for root, dirs, files in os.walk(path):
#          for file in files:
#              file_path = os.path.join(root, file)
# 
#              if file.endswith('.txt'):
#                  loaders.append(TextLoader(file_path))
#              elif file.endswith('.pdf'):
#                  loaders.append(PyPDFLoader(file_path))
#              elif file.endswith('.csv'):
#                  loaders.append(CSVLoader(file_path))  
#              elif file.endswith('.py'):
#                  loaders.append(PythonLoader(file_path))
#              elif file.endswith('.jpeg') or file.endswith('.png'):
#                 loaders.append(UnstructuredImageLoader(file_path))

#    return loaders

def _get_file_paths(path:str)->Iterator[str]:
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            yield file_path

def _get_file_extension(file_name: str) -> str:
    file_root, file_extension = os.path.splitext(file_name)
    return file_extension

_loader_by_filetype:dict[BaseLoader] = {
    ".txt": TextLoader,
    ".pdf": PyPDFLoader,
    ".csv": CSVLoader,
    ".py": PythonLoader,
    ".jpeg": UnstructuredImageLoader,
    ".png": UnstructuredImageLoader,
}
_docu_splitter_by_filetype = {
   ".txt": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
   ".pdf": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
   ".csv": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
   ".py": lambda: PythonCodeTextSplitter(chunk_size = 1000, chunk_overlap =0),
   ".jpeg": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
   ".png": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
}


def get_docs_from_file(file_path:str)->list:
    file_ext = _get_file_extension(file_path)
    if not file_ext in _loader_by_filetype:
        return [] # Unsupported file

    docs = _loader_by_filetype[file_ext](file_path).load()
    subdocs = _docu_splitter_by_filetype[file_ext]().split_documents(docs)
    return subdocs
    
 
def get_docs_from_path(path, docs):
    for file_path in _get_file_paths(path):
        docs.extend(get_docs_from_file(file_path))
    return docs
    
if __name__ == "__main__":
   for doc in get_docs_from_path("test/data"):
       print(doc)