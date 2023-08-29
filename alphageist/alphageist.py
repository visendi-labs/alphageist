import threading
import logging
import os
import shutil
from pathlib import Path
from typing import (
    Optional,
    Callable
)

from langchain.callbacks.base import BaseCallbackHandler

from alphageist import state as s
from alphageist.vectorstore import VectorStore
from alphageist import constant
from alphageist import query
from alphageist import errors
from alphageist import config as cfg
from alphageist import util
from alphageist import callbackhandler

logger = logging.getLogger(constant.LOGGER_NAME)

STATE_SUBSCRIPTION_SIGNATURE = Callable[[s.State, s.State], None]

def get_config()->cfg.Config:
    return cfg.load_config(constant.CONFIG_PATH, cfg.get_default_config())

class Alphageist(util.StateSubscriptionMixin):
    vectorstore: VectorStore
    exception: Optional[Exception]
    config: cfg.Config

    def __init__(self):
        super().__init__()
        self._state = s.NEW
        self.exception = None
        self.vectorstore = VectorStore()
        self.vectorstore.subscribe_to_statechange(self.on_vectorstor_state_change)

    @util.allowed_states({s.NEW})
    def load_config(self):
        try:
            self.config = get_config()
        except Exception as e:
            logger.exception("Error loading config")
            self.state = s.ERROR
            self.exception = e
            return

        if not isinstance(self.config, cfg.Config):
            raise ValueError(f"config has to be of type config.Config not {type(self.config)}")

        try:
            self.config.check()
        except (errors.MissingConfigComponentsError, 
                errors.MissingConfigValueError,
                errors.ConfigValueError) as e:
            self.exception = e
            self.state = s.ERROR
        except Exception as e:
            raise e
            self.state = s.ERROR
        else:
            if cfg.LOG_LEVEL in self.config:
                log_lvl = self.config[cfg.LOG_LEVEL]
                logger.info(f"Setting loglevel to {log_lvl}")
                util.set_logging_level(log_lvl)
            self.state = s.CONFIGURED

    @util.allowed_states({s.CONFIGURED})        
    def start_init_vectorstore(self)->Optional[util.LoadingContext]:
        self.vectorstore.start_init_vectorstore(self.config)
        return self.vectorstore.loading_ctx

    @util.allowed_states({s.LOADING_VECTORSTORE})
    def finish_init_vectorstore(self)->None:
        self.state = s.STANDBY

    @util.allowed_states({s.STANDBY})
    def start_search(self, query_string:str, callbacks: list[BaseCallbackHandler] = [])->None:
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

    @util.allowed_states({s.NEW, s.CONFIGURED, s.STANDBY, s.ERROR, s.LOADING_VECTORSTORE})
    def reset(self):
        self.exception = None
        self.vectorstore.reset()
        self.state = s.NEW

    def on_vectorstor_state_change(self, old_state: s.State, new_state: s.State)->None:
        if new_state is s.ERROR:
            self.exception = self.vectorstore.exception
            self.state = s.ERROR
        elif new_state is s.LOADING:
            self.state = s.LOADING_VECTORSTORE
        elif new_state is s.LOADED and old_state is s.LOADING:
            self.finish_init_vectorstore()

    def on_config_changed(self):
        self.reset() 




    
    

    