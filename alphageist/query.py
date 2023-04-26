from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma

def query_docs(docs, query) -> dict: 

    embedding = OpenAIEmbeddings()
    vectorStore = Chroma.from_documents(docs, embedding=embedding)
    index = VectorStoreIndexWrapper(vectorstore=vectorStore)

    llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")
    return index.query_with_sources(query, llm=llm)
