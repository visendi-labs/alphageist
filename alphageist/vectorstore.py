import os
import threading
import logging
from typing import Optional
from platformdirs import user_config_dir

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.qdrant import Qdrant
import qdrant_client

from langchain import chat_models
from langchain.vectorstores.base import VectorStore as LangchainVectorstore
from langchain.callbacks.base import BaseCallbackHandler
from langchain.indexes.vectorstore import VectorStoreIndexWrapper

from alphageist.doc_generator import get_docs_from_path
from alphageist.util import allowed_states
from alphageist import util
from alphageist import state
from alphageist import errors
from alphageist import constant

import alphageist.config as cfg

logger = logging.getLogger(constant.LOGGER_NAME)

COLLECTION_NAME = "alphageist"

class VectorStore(util.StateSubscriptionMixin):
    exception: Exception
    store: Optional[Qdrant]
    emb: Embeddings
    _thread: threading.Thread

    def __init__(self):
        super().__init__()
        self._state = state.NEW
        self.store = None
        self._thread = None
        
    def is_created(self)->bool:
        if self.store is None:
            return False
        if not COLLECTION_NAME in [c.name for c in self.store.client.get_collections().collections]:
            return False
        if not self.store.client.count(COLLECTION_NAME).count > 0:
            return False
        return True

    @allowed_states({state.NEW})
    def start_init_vectorstore(self, config:cfg.Config, emb:Optional[Embeddings]=None):
        self.emb = get_embeddings(config) if emb is None else emb
        if self.store is not None: 
            del self.store
            self.store = None
        client = qdrant_client.QdrantClient(path=config[cfg.VECTORDB_DIR], prefer_grpc=True)  
        self.store = Qdrant(client=client, collection_name=COLLECTION_NAME, embeddings=self.emb)  

        self.state = state.LOADING

        vector_db_path = config[cfg.VECTORDB_DIR]

        if self.is_created():
            self.state = state.LOADED
        else:
            self._thread = threading.Thread(target=self._create_vectorstore, args = (config,))
            self._thread.daemon = True # Should this really be true?
            self._thread.start()

    def _create_vectorstore(self, config: cfg.Config) -> None:
        search_dir = config[cfg.SEARCH_DIRS]
        docs = get_docs_from_path(search_dir)
        if not docs:
            self.exception = errors.NoSupportedFilesInDirectoryError(search_dir)
            self.state = state.ERROR 
            return

        vector_db_dir = config[cfg.VECTORDB_DIR]

        logger.info(f"Creating vectorstore for {len(docs)} documents using {self.emb.__class__.__name__}")
        del self.store
        self.store = None
        try:
            self.store = Qdrant.from_documents(docs, 
                                           embedding=self.emb,
                                           collection_name=COLLECTION_NAME, 
                                           path=vector_db_dir)
  
        except Exception as e:
            logger.exception(f"Unable to create vectorstore: {str(e)}")
            self.exception = e
            self.state = state.ERROR
        else:
            logger.info("Vectorstore successfully created")
            self.state = state.LOADED

    @allowed_states({state.LOADED, state.ERROR, state.NEW})
    def reset(self):
        if self.store is not None:
            self.store.client.delete_collection(collection_name=COLLECTION_NAME)
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

    @allowed_states({state.LOADED})
    def query(self, 
             config: cfg.Config, 
             query_string: str, 
             callbacks: list[BaseCallbackHandler] = [] ) -> dict:

        index = self._get_vectorstore_index_wrapper()
        streaming = bool(callbacks)
        llm = chat_models.ChatOpenAI(temperature=config[cfg.LLM_TEMPERATURE], # type: ignore
                             model_name=config[cfg.LLM_MODEL_NAME],
                             streaming=streaming, 
                             callbacks=callbacks, 
                             openai_api_key=config[cfg.API_KEY_OPEN_AI])
        logger.info(
            f"Querying using {config[cfg.LLM_MODEL_NAME]} on temp {config[cfg.LLM_TEMPERATURE]} (streaming: {streaming})")

        try:
            res = index.query_with_sources(query_string, llm=llm)
        except Exception as err:
            self.exception = err
            self.state = state.ERROR
            res = {}
        return res
    

def get_embeddings(config: cfg.Config) -> Embeddings:
    """This function returns the proper Embeddings according
    to the config"""
    return OpenAIEmbeddings(openai_api_key=config[cfg.API_KEY_OPEN_AI]) #type: ignore