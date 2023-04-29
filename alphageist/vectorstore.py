import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma
from .doc_generator import get_docs_from_path

LOCAL_DB_DIR = ".alphageist"

def vectorstore_exists() -> bool:
    return os.path.exists(LOCAL_DB_DIR)

def load_vectorstore()->Chroma:
    embedding = OpenAIEmbeddings()
    client = Chroma(embedding_function=embedding, persist_directory=LOCAL_DB_DIR)
    return client

def get_vectorstore(path: str)->Chroma:
    docs = get_docs_from_path(path)
    embedding = OpenAIEmbeddings()
    return Chroma.from_documents(docs, embedding=embedding, persist_directory=LOCAL_DB_DIR)
