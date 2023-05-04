import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma
from .doc_generator import get_docs_from_path


def vectorstore_exists(persist_directory:str) -> bool:
    return os.path.exists(persist_directory)

def load_vectorstore(persist_directory:str)->Chroma:
    embedding = OpenAIEmbeddings()
    client = Chroma(embedding_function=embedding, persist_directory=persist_directory)
    return client

def create_vectorstore(path: str, persist_directory:str)->Chroma:
    docs = get_docs_from_path(path)
    if not docs:
        raise ValueError(f"No supported files found in {path}")
    embedding = OpenAIEmbeddings()
    return Chroma.from_documents(docs, embedding=embedding, persist_directory=persist_directory)

