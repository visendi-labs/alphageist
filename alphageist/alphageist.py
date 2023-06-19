import threading
import logging
import os
import shutil
import typing

from langchain.callbacks.base import BaseCallbackHandler
import chromadb # type: ignore

from alphageist import state as s
from alphageist.vectorstore import vectorstore_exists
from alphageist.vectorstore import load_vectorstore
from alphageist.vectorstore import VectorStore
from alphageist import constant
from alphageist import query
from alphageist import errors
from alphageist import config as cfg
from alphageist import util
from alphageist import callbackhandler

logger = logging.getLogger(constant.LOGGER_NAME)

STATE_SUBSCRIPTION_SIGNATURE = typing.Callable[[s.State, s.State], None]

def get_config()->cfg.Config:
    cfg_file = cfg.get_config_file_path()
    return cfg.load_config(cfg_file, cfg.get_default_config())

class Alphageist(util.StateSubscriptionMixin):
    vectorstore: VectorStore
    exception: Exception
    config: cfg.Config

    def __init__(self):
        super().__init__()
        self._state = s.NEW
        self.reset()

    def load_config(self):
        try:
            config: cfg.Config = get_config()
        except Exception as e:
            logger.exception("Error loading config")
            self.state = s.ERROR
            self.exception = e
            return

        if not isinstance(config, cfg.Config):
            raise ValueError(f"config has to be of type config.Config not {type(config)}")

        self.config = config

        try:
            config.assert_has_required_keys()
        except (errors.MissingConfigComponentsError, errors.MissingConfigValueError) as e:
            self.exception = e
            self.state = s.ERROR
        except Exception as e:
            raise e
            self.state = s.ERROR
        else:
            self.state = s.CONFIGURED

    def start_init_vectorstore(self)->None:
        if self.state is not s.CONFIGURED:
            raise errors.InvalidStateError(self.state, {s.CONFIGURED})
        self.vectorstore.start_init_vectorstore(self.config)
        self.state = s.LOADING_VECTORSTORE

    def finish_init_vectorstore(self)->None:
        if self.state is not s.LOADING_VECTORSTORE:
            raise errors.InvalidStateError(self.state, {s.LOADING_VECTORSTORE})

        self.state = s.STANDBY

    def start_search(self, query_string:str, callbacks: list[BaseCallbackHandler] = [])->None:
        if self.state is not s.STANDBY:
            raise errors.InvalidStateError(self.state, {s.STANDBY}) 

        if not query_string:
            raise ValueError("Search string cannot be empty")

        def on_llm_finish(response, **kwargs):
            self.state = s.STANDBY

        cbh = callbackhandler.CustomStreamHandler(
            on_llm_new_token=lambda *args, **kwargs:None,
            on_llm_end=on_llm_finish,
        )
        callbacks.append(cbh)

        query_thread = threading.Thread(
            target=self.vectorstore.query, 
            args=(self.config, query_string),
            kwargs={'callbacks':callbacks},
            daemon=True)
        logger.info(f"starting search for: {query_string}")
        query_thread.start()
        self.state = s.QUERYING

    def reset(self):
        allowed_states = {s.NEW, s.CONFIGURED, s.STANDBY, s.ERROR}
        if not self.state in allowed_states:
            raise errors.InvalidStateError(self.state, allowed_states)
        self.exception = None
        self.vectorstore = VectorStore()
        self.vectorstore.subscribe_to_statechange(self.on_vectorstor_state_change)
        self.state = s.NEW

    def on_vectorstor_state_change(self, old_state: s.State, new_state: s.State)->None:
        if new_state is s.ERROR:
            self.exception = self.vectorstore.exception
            self.state = s.ERROR
        elif new_state is s.LOADED and old_state is s.LOADING:
            self.state = s.STANDBY

    def on_config_changed(self):
        # Remove database directory
        if os.path.exists(self.config[cfg.VECTORDB_DIR]):
            shutil.rmtree(self.config[cfg.VECTORDB_DIR])
        self.reset() 




    
    

    