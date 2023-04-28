from .doc_generator import get_docs_from_path
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma

def vectorstore_exists(path:str)->bool:
    raise NotImplementedError

def generate_vectorstore(path:str):
    raise NotImplementedError

def get_vectorstore(path: str)->Chroma:
    docs = get_docs_from_path(path)
    embedding = OpenAIEmbeddings()
    return Chroma.from_documents(docs, embedding=embedding, persist_directory=".")
