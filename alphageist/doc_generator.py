import os 
import logging
from typing import (
    Any,
    Optional
)
from collections.abc import Iterator

from pathlib import Path

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter, PythonCodeTextSplitter
from langchain.document_loaders.base import BaseLoader
from langchain_community.document_loaders import (
    PyPDFLoader,
    PythonLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredExcelLoader,
    CSVLoader
)

from alphageist.custom_loaders import PPTXLoader
from alphageist.util import (
    is_temp_file,
    string_to_raw_string,
    LoadingContext
)
from alphageist import constant
from alphageist.errors import LoadingCancelled

logger = logging.getLogger(constant.LOGGER_NAME)

def _get_file_paths(path:Path)->Iterator[str]:
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            yield file_path

def _get_file_extension(file_name: str) -> str:
    file_root, file_extension = os.path.splitext(file_name)
    return file_extension

_loader_by_filetype:dict[str,Any] = {
    ".txt": lambda file_path: TextLoader(file_path, autodetect_encoding=True),
    ".pdf": PyPDFLoader,
    ".csv": lambda file_path: CSVLoader(file_path, csv_args={ 'delimiter': ',' }),
    ".py": PythonLoader,
    ".go": lambda file_path: TextLoader(file_path, autodetect_encoding=True),
    ".pptx": PPTXLoader,
    ".docx": Docx2txtLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
}
_docu_splitter_by_filetype = {
    ".txt": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
    ".pdf": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
    ".csv": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
    ".py": lambda: PythonCodeTextSplitter(chunk_size = 1000, chunk_overlap =0),
    ".go": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
    ".pptx": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
    ".docx": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
    ".xlsx": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
    ".xls": lambda: RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap =0),
}

def get_docs_from_file(file_path:str)->list[Document]:
    file_ext = _get_file_extension(file_path)
    if is_temp_file(file_path):
        return [] # Skip temporary files
    if not file_ext in _loader_by_filetype:
        return [] # Unsupported file
    logger.info(f"Loading {file_path}")
    try:
        docs = _loader_by_filetype[file_ext](file_path).load()
    except Exception as e:
        logger.exception(f"Exception encountered while loading file {file_path}: {e}")
        return []  # return an empty list if the file is damaged
    subdocs = _docu_splitter_by_filetype[file_ext]().split_documents(docs)
    return subdocs

def get_docs_from_path(path, ctx:Optional[LoadingContext])->list[Document]:
    docs = []
    if ctx is not None:
        ctx.total_files = sum(1 for _ in _get_file_paths(path))
    files_loaded = -1

    for file_path in _get_file_paths(path):
        if ctx is not None:
            if ctx.is_cancelled():
                raise LoadingCancelled
            ctx.current_file = file_path
            ctx.files_loaded += 1
        docs.extend(get_docs_from_file(file_path))
    return _escape_unicode(docs)

def _escape_unicode(docs:list[Document])->list[Document]:
    docs = docs[:]
    for doc in docs:
        doc.page_content = string_to_raw_string(doc.page_content)
    return docs
