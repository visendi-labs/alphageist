from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma
from alphageist.doc_generator import get_loaders

def query_files(query: str, path: str):
    """Old function"""
    llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")
    loaders = get_loaders(path)
    if len(loaders) == 0:
        raise Exception("error: no loaders found")

    print(f"Number of loaders: {len(loaders)}\n")
    index = VectorstoreIndexCreator().from_loaders(loaders)

    response = index.query_with_sources(query, llm=llm)
    response["answer"] = response["answer"].rstrip("\n") # Remove trailing newline character

    return response

    
def query_docs(docs, query) -> dict: 

    embedding = OpenAIEmbeddings()
    vectorStore = Chroma.from_documents(docs, embedding=embedding)
    index = VectorStoreIndexWrapper(vectorstore=vectorStore)

    llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")
    return index.query_with_sources(query, llm=llm)