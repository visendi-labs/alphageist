import os
import threading
import logging
import typing
from platformdirs import user_config_dir

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.chroma import Chroma
from langchain import chat_models
from langchain.vectorstores.base import VectorStore as LangchainVectorstore
from langchain.callbacks.base import BaseCallbackHandler
from langchain.indexes.vectorstore import VectorStoreIndexWrapper

from alphageist.doc_generator import get_docs_from_path
from alphageist import util
from alphageist import state
from alphageist import errors
from alphageist import constant

import alphageist.config as cfg

logger = logging.getLogger(constant.LOGGER_NAME)

LLM_MODEL_NAME = "gpt-3.5-turbo"
TEMPERATURE = 0.0
class VectorStore(util.StateSubscriptionMixin):
    exception: Exception
    store: LangchainVectorstore

    def __init__(self):
        super().__init__()
        self._state = state.NEW
        self.reset()

    def start_init_vectorstore(self, config):
        if self.state is not state.NEW:
            raise errors.InvalidStateError(self.state, {state.NEW})

        self.state = state.LOADING

        vector_db_path = config[cfg.VECTORDB_DIR]
        thread: threading.Thread

        if vectorstore_exists(vector_db_path):
           thread =  threading.Thread(target=self._load_vectorstore,
                                      args = (config,))
        else:
            thread = threading.Thread(target=self._create_vectorstore,
                                      args = (config,))

        thread.daemon = True
        thread.start()

    def _create_vectorstore(self, config: cfg.Config):
        try:
            self.store = create_vectorstore(config)
        except Exception as e:
            logger.exception(f"Unable to create vectorstore: {str(e)}")
            self.exception = e
            self.state = state.ERROR
        else:
            logger.info("Vectorstore successfully created")
            self.state = state.LOADED

    def _load_vectorstore(self, config: dict):
        try:
            self.store = load_vectorstore(config)
        except Exception as e:
            logger.exception(f"Unable to load vectorstore: {str(e)}")
            self.exception = e
            self.state = state.ERROR
        else:
            self.state = state.LOADED

    def reset(self):
        allowed_states = {state.LOADED, state.ERROR, state.NEW}
        if self.state not in allowed_states:
            raise errors.InvalidStateError(self.state, allowed_states)
        self.exception = None
        self.state = state.NEW

    def _get_vectorstore_index_wrapper(self):
        try:
            index = VectorStoreIndexWrapper(vectorstore=self.store)
        except Exception as err:
            logger.error(
                f"unable to create VectorStoreIndexWrapper using vectorstore: {VectorStore}")
            self.state = state.ERROR
            raise err
        return index

    def _get_llm(self, *args, **kwargs):
        try:
            llm = ChatOpenAI(*args, **kwargs)
        except Exception as err:
            logger.error(f"unable to create a llm instance")
            self.state = state.ERROR
            raise err

    def query(self, 
             config: cfg.Config, 
             query_string: str, 
             callbacks: list[BaseCallbackHandler] = [] ) -> dict:

        if self.state is not state.LOADED:
            raise errors.InvalidStateError(self.state, {state.LOADED})

        index = self._get_vectorstore_index_wrapper()
        streaming = bool(callbacks)
        llm = chat_models.ChatOpenAI(temperature=TEMPERATURE, # type: ignore
                             model_name=LLM_MODEL_NAME,
                             streaming=streaming, 
                             callbacks=callbacks, 
                             openai_api_key=config[cfg.API_KEY_OPEN_AI])
        logger.debug(
            f"Querying using {LLM_MODEL_NAME} on temp {TEMPERATURE} (streaming: {streaming})")

        try:
            res = index.query_with_sources(query_string, llm=llm)
        except Exception as err:
            self.exception = err
            self.state = state.ERROR
            res = {}
        return res
        

def vectorstore_exists(persist_directory: str) -> bool:
    """This function checks if the vectorstore already 
    exists at the specified directory"""
    return os.path.exists(persist_directory)


def get_embeddings(config: cfg.Config) -> Embeddings:
    """This function returns the proper Embeddings according
    to the config"""
    if not cfg.API_KEY_OPEN_AI in config.keys():
        raise errors.MissingConfigComponentsError({cfg.API_KEY_OPEN_AI})
    
    return OpenAIEmbeddings(openai_api_key=config[cfg.API_KEY_OPEN_AI]) #type: ignore


def get_vectorstore_path(config:cfg.Config)->str:
    """This function returns the path to the vector DB
     based on the operating system"""
    if not cfg.VECTORDB_DIR in config.keys():
        raise errors.MissingConfigComponentsError({cfg.VECTORDB_DIR})
    vector_db_dir = config[cfg.VECTORDB_DIR]
    if not vector_db_dir:
        raise ValueError("No directory provided for persisting db")
    if not util.path_is_valid_format(vector_db_dir):
        raise ValueError("{vector_db_dir} is not a valid directory")
    return vector_db_dir
    

def load_vectorstore(config: cfg.Config) -> Chroma:
    """This function loads the vectorstore from the specified directory"""
    embedding = get_embeddings(config)
    vector_db_dir = get_vectorstore_path(config)
    logger.info(f"Loading vectorstore from {vector_db_dir}...")
    client = Chroma(embedding_function=embedding, persist_directory=vector_db_dir)
    return client


def create_vectorstore(config: cfg.Config) -> Chroma:
    """This function creates the vectorstore from 
    the documents found in the specified directory"""
    if not cfg.SEARCH_DIRS in config.keys():
        raise errors.MissingConfigComponentsError({cfg.SEARCH_DIRS})

    search_dir = config[cfg.SEARCH_DIRS]
    if not util.path_is_valid_format(search_dir):
        raise ValueError(f"{search_dir} is not a valid directory")

    docs = get_docs_from_path(search_dir)

    if not docs:
        raise ValueError(f"No supported files found in {search_dir}")

    vector_db_dir = get_vectorstore_path(config)

    embedding = get_embeddings(config)
    logger.info(f"Creating vectorstore...")
    client = Chroma.from_documents(docs, embedding=embedding, persist_directory=vector_db_dir)
    logger.info(f"Saving vectorstore to {vector_db_dir}")
    client.persist() # Save DB
    return client