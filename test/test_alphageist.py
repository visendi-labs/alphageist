from typing import (
    Optional,
    List,
    Any,
    Mapping
)
import threading
import json
import platformdirs
import shutil
import pytest
from pathlib import Path
from unittest.mock import (
    Mock, 
    MagicMock, 
    patch,
    create_autospec
)
from alphageist.alphageist import Alphageist
from alphageist.vectorstore import VectorStore
from alphageist import (
    state,
    errors,
    config as cfg,
    constant
)

from test.test_vectorstore import MockEmbedding
import test.test_config as test_cfg

from langchain.chat_models.base import SimpleChatModel
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema.messages import BaseMessage

from qdrant_client import QdrantClient

class MockLMM(SimpleChatModel):
    @property
    def _llm_type(self) -> str: return "MockLLM"

    def _call(self,*args, **kwargs) -> str:
        return "HELLO MOTHERFUCKER"

@pytest.fixture
def tmp_user_config_dir(tmp_path):
    """Updates the config path to a tmp_path"""
    # Save the original values
    original_config_path = constant.CONFIG_PATH

    # Update CONFIG_PATH based on the new APP_DATA_DIR
    constant.CONFIG_PATH = tmp_path / "config.json"

    yield tmp_path

    # Restore the original values after the test runs
    constant.CONFIG_PATH = original_config_path

@pytest.fixture
def tmp_env_factory(tmp_user_config_dir):
    """Generates a temporary environment/directory for the test.
    If cfg_name is passed as argument it will copy that specific
    config file from test/config folder and it will be named config.cfg.

    If the VECTORDB_DIR parameter in the config is set to something this 
    value will be changed to the root level of the temporary folder.
    """
    def _tmp_env_factory(cfg_name: Optional[str] = None):
        if cfg_name:
            root_dir = Path(".")
            config_dir = root_dir / 'test' / 'config'

            # Try to update to parse the config and change the vector db dir 
            # to the temporary test path. For cases where we want to have a broken
            # non parsable config we simply copy it to the temp path.
            try:
                config = cfg.load_config(config_dir / cfg_name)
            except:
                shutil.copy2(config_dir / cfg_name, tmp_user_config_dir / 'config.json')
            else:
                if cfg.VECTORDB_DIR in config:
                    config[cfg.VECTORDB_DIR] = str(tmp_user_config_dir)
                cfg.save_config(tmp_user_config_dir / 'config.json', config)
        yield tmp_user_config_dir
    return _tmp_env_factory

def test_first_state_is_new():
    a = Alphageist()
    assert a.state is state.NEW

@pytest.mark.parametrize("inval_state", {
    state.CONFIGURED, 
    state.LOADING_VECTORSTORE, 
    state.STANDBY,
    state.QUERYING,
    state.ERROR})
def test_load_config_invalid_state(inval_state: state.State):
    a = Alphageist()
    a.state = inval_state
    with pytest.raises(errors.InvalidStateError):
        a.load_config()

@pytest.mark.parametrize('cfg_name, exp_state, exp_exception', [
    ('valid.json', state.CONFIGURED, None),
    ('invalid_format_config.json', state.ERROR, json.decoder.JSONDecodeError),
    ('open_ai_key_missing.json', state.ERROR, errors.MissingConfigValueError),  
])
def test_load_config(tmp_env_factory, cfg_name, exp_state, exp_exception):
    tmp_dir = next(tmp_env_factory(cfg_name))
    a = Alphageist()
    a.load_config()

    assert a.state is exp_state
    if exp_exception is None:
        assert a.exception is None
    else:
        assert isinstance(a.exception, exp_exception)

def test_start_load_vectorstore_incorrect_state():
    a = Alphageist()
    with pytest.raises(errors.InvalidStateError):
        a.start_init_vectorstore()

@pytest.mark.parametrize("inval_state", {
    state.NEW, 
    state.LOADING_VECTORSTORE, 
    state.STANDBY,
    state.QUERYING,
    state.ERROR})
def test_start_init_vectorstore_incorrect_state(inval_state: state.State):
    a = Alphageist()
    a.state = inval_state
    with pytest.raises(errors.InvalidStateError):
        a.start_init_vectorstore()

@patch('alphageist.vectorstore.OpenAIEmbeddings', new=MockEmbedding)
def test_start_init_vectorstore_create_new(tmp_env_factory):
    next(tmp_env_factory('valid.json'))

    a = Alphageist()
    a.load_config()
    a.start_init_vectorstore()

    assert a.state is state.LOADING_VECTORSTORE 
    a.vectorstore._thread.join() # Wait for loading to finish
    assert a.state is state.STANDBY

@patch('alphageist.vectorstore.OpenAIEmbeddings', new=MockEmbedding)
def test_start_init_vectorstore_load_existing(tmp_env_factory):
    next(tmp_env_factory('valid_tiny.json'))

    a = Alphageist()
    a.load_config()
    a.start_init_vectorstore()
    a.vectorstore._thread.join() # Wait for loading to finish
    del a.vectorstore.store.client

    a = Alphageist()
    a.load_config()
    a.start_init_vectorstore()
    assert a.state is state.STANDBY
    
@pytest.mark.parametrize("inval_state", {
    state.NEW, 
    state.CONFIGURED,
    state.LOADING_VECTORSTORE, 
    state.QUERYING,
    state.ERROR})
def test_start_search_incorrect_state(inval_state: state.State):
    a = Alphageist()
    a.state = inval_state
    with pytest.raises(errors.InvalidStateError):
        a.start_search("hej")


@patch('alphageist.vectorstore.OpenAIEmbeddings', new=MockEmbedding)
def test_start_search_empty_search_string(tmp_env_factory):
    next(tmp_env_factory('valid_tiny.json'))
    a = Alphageist()
    a.load_config()
    a.start_init_vectorstore()
    a.vectorstore._thread.join()

    with pytest.raises(ValueError):
        a.start_search("")

@patch('alphageist.vectorstore.OpenAIEmbeddings', new=MockEmbedding)
@patch('alphageist.vectorstore.ChatOpenAI', new=MockLMM)
@patch('alphageist.vectorstore.QdrantClient', new=create_autospec(QdrantClient))
def test_start_search(tmp_env_factory):
    next(tmp_env_factory('valid_tiny.json'))
    a = Alphageist()
    a.load_config()
    a.start_init_vectorstore()
    a.vectorstore._thread.join()

    # Wait for state to change
    e = threading.Event()
    a.subscribe_to_statechange(lambda _, new_state: e.set() if new_state is not state.QUERYING else None)
    a.start_search("hej hej")
    assert a.state is state.QUERYING
    e.wait()
    assert a.state is state.STANDBY

def test_reset_standby_state(tmp_env_factory):
    next(tmp_env_factory('valid_tiny.json'))
    a = Alphageist()
    a.load_config()
    a.reset()

    assert a.state is state.NEW
    assert a.exception is None
    assert a.vectorstore.is_created() == False

def test_reset_loading_state(tmp_env_factory):
    next(tmp_env_factory('valid.json'))
    a = Alphageist()
    a.load_config()
    ctx = a.start_init_vectorstore()

    assert a.state is state.LOADING_VECTORSTORE, "Unable to continue with test: wrong state"
    import time
    time.sleep(1.0)
    a.reset()

    assert a.state is state.NEW
    assert a.exception is None
    assert a.vectorstore.is_created() == False


@pytest.mark.parametrize("inval_state", {
    state.QUERYING})
def test_reset_incorrect_state(inval_state:state.State):
    a = Alphageist()
    a.state = inval_state
    with pytest.raises(errors.InvalidStateError):
        a.reset()
