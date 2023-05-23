import sys
import logging
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
from langchain.vectorstores.base import VectorStore

LLM_MODEL_NAME = "gpt-3.5-turbo"
TEMPERATURE = 0.0


def query_vectorstore(vectorstore:VectorStore, query:str, callbacks:list[BaseCallbackHandler] = []) -> dict:
    try:
        index = VectorStoreIndexWrapper(vectorstore=vectorstore)
    except error as err:
        logging.error(f"unable to create VectorStoreIndexWrapper using vectorstore: {VectorStore()}")
        raise err

    streaming = bool(callbacks)
    try:
        llm = ChatOpenAI(temperature=TEMPERATURE, model_name=LLM_MODEL_NAME, streaming=streaming, callbacks=callbacks)
    except error as err:
        logging.error(f"unable to create a llm instance")
        raise err

    logging.debug(f"Querying using {LLM_MODEL_NAME} on temp {TEMPERATURE} (streaming: {streaming})")
    
    try:
        res =  index.query_with_sources(query, llm=llm)
    except error as err:
        logging.error(f"unable to query llm")
        raise err
    
    return res
