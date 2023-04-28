from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings

def query_vectorstore(vectorstore, query):
    index = VectorStoreIndexWrapper(vectorstore=vectorstore)
    embedding = OpenAIEmbeddings()
    llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")
    return index.query_with_sources(query, llm=llm)
