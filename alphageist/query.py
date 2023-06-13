import re
import sys
import logging
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
from langchain.vectorstores.base import VectorStore
from alphageist import config as cfg

def get_sources_from_answer(answer: str) -> list[str]:
        if re.search(r"SOURCES:\s", answer):
            _, sources = re.split(r"SOURCES:\s", answer)
        else:
            sources = ""
        return sources.split(',')

def query_vectorstore(vectorstore: VectorStore, 
                      query: str, 
                      config:dict,
                      callbacks: list[BaseCallbackHandler] = [], 
                      ) -> dict:
    try:
        index = VectorStoreIndexWrapper(vectorstore=vectorstore)
    except Exception as err:
        logging.error(
            f"unable to create VectorStoreIndexWrapper using vectorstore: {VectorStore}")
        raise err

    streaming = bool(callbacks)
    try:
        llm = ChatOpenAI(temperature=config[cfg.LLM_TEMPERATURE], 
                         model_name=config[cfg.LLM_MODEL_NAME],
                         streaming=streaming, 
                         callbacks=callbacks, 
                         openai_api_key=config[cfg.API_KEY_OPEN_AI])
    except Exception as err:
        logging.error(f"unable to create a llm instance")
        raise err

    logging.debug(
        f"Querying using {config[cfg.LLM_MODEL_NAME]} on temp {config[cfg.LLM_TEMPERATURE]} (streaming: {streaming})")
    
    try:
        res = index.query_with_sources(query, llm=llm)
    except Exception as err:
        logging.error(f"unable to query llm")
        raise err

    return res
