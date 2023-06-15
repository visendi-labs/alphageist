from os import path
import pytest

from langchain.embeddings.base import Embeddings

from alphageist.vectorstore import VectorStore
from alphageist.vectorstore import create_vectorstore
from alphageist.vectorstore import load_vectorstore
from alphageist.vectorstore import get_embeddings
from alphageist import errors
from alphageist import config as cfg
from alphageist import state


empty_dir_path = path.join("test", "data", "empty_folder")
test_data = path.join("test", "data")

test_cfg_with_api_key = {cfg.API_KEY_OPEN_AI: "abc123"}
test_cfg = {cfg.API_KEY_OPEN_AI: "abc123",
            cfg.VECTORDB_DIR: ".",
            cfg.SEARCH_DIRS: test_data}

def test_vectorstore_first_state_is_new():
    v = VectorStore()
    assert v.state is state.NEW

def test_start_init_vectorstore_incorrect_state():
    v = VectorStore()
    v.state = state.ERROR
    with pytest.raises(errors.InvalidStateError):
        v.start_init_vectorstore(test_cfg)

def test_reset():
    v = VectorStore()
    v.state = state.ERROR
    v.reset()
 
def test_reset_incorrect_sate():
    v = VectorStore()
    v.state = state.LOADING
    with pytest.raises(errors.InvalidStateError):
        v.reset()

def test_get_embeddings_no_api_key_in_cfg_error():
    with pytest.raises(errors.MissingConfigComponentsError) as exc_info:
        get_embeddings({})
    assert cfg.API_KEY_OPEN_AI in str(exc_info.value)


def test_get_embeddings_correct_type():
    e = get_embeddings(test_cfg_with_api_key)
    assert isinstance(e, Embeddings)


def test_create_vectorstore_no_search_dirs_in_cfg_error():
    with pytest.raises(errors.MissingConfigComponentsError) as exec_info:
        config = test_cfg.copy()
        config.pop(cfg.SEARCH_DIRS)
        create_vectorstore(config)
    assert cfg.SEARCH_DIRS in str(exec_info.value)

def test_create_vectorstore_no_vectore_store_in_cfg_error():
    with pytest.raises(errors.MissingConfigComponentsError) as exec_info:
        config = test_cfg.copy()
        config.pop(cfg.VECTORDB_DIR)
        create_vectorstore(config)
    assert cfg.VECTORDB_DIR in str(exec_info.value)

def test_get_docs_from_file_non_existing():
    with pytest.raises(ValueError) as exc_info:
        config = test_cfg.copy()
        config[cfg.SEARCH_DIRS]= empty_dir_path
        create_vectorstore(config)
