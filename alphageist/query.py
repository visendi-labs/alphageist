import sys
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
from langchain.vectorstores.base import VectorStore



def query_vectorstore(vectorstore:VectorStore, query:str, callbacks:list[BaseCallbackHandler] = []):
    index = VectorStoreIndexWrapper(vectorstore=vectorstore)

    streaming = bool(callbacks)
    llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo", streaming=streaming, callbacks=callbacks)
    return index.query_with_sources(query, llm=llm)
