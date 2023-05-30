from os import path
import pytest

from langchain.embeddings.base import Embeddings

from alphageist.vectorstore import create_vectorstore
from alphageist.vectorstore import load_vectorstore
from alphageist.vectorstore import get_embeddings
from alphageist.errors import MissingConfigComponentError
from alphageist import config as cfg


empty_dir_path = path.join("test", "data", "empty_folder")
test_data = path.join("test", "data")

test_cfg_with_api_key = {cfg.API_KEY_OPEN_AI: "abc123"}
test_cfg = {cfg.API_KEY_OPEN_AI: "abc123",
            cfg.VECTORDB_DIR: ".",
            cfg.SEARCH_DIRS: test_data}


def test_get_embeddings_no_api_key_in_cfg_error():
    with pytest.raises(MissingConfigComponentError) as exc_info:
        get_embeddings({})
    assert cfg.API_KEY_OPEN_AI in str(exc_info.value)


def test_get_embeddings_correct_type():
    e = get_embeddings(test_cfg_with_api_key)
    assert isinstance(e, Embeddings)


def test_create_vectorstore_no_search_dirs_in_cfg_error():
    with pytest.raises(MissingConfigComponentError) as exec_info:
        config = test_cfg.copy()
        config.pop(cfg.SEARCH_DIRS)
        create_vectorstore(config)
    assert cfg.SEARCH_DIRS in str(exec_info.value)

def test_create_vectorstore_no_vectore_store_in_cfg_error():
    with pytest.raises(MissingConfigComponentError) as exec_info:
        config = test_cfg.copy()
        config.pop(cfg.VECTORDB_DIR)
        create_vectorstore(config)
    assert cfg.VECTORDB_DIR in str(exec_info.value)

def test_get_docs_from_file_non_existing():
    with pytest.raises(ValueError) as exc_info:
        config = test_cfg.copy()
        config[cfg.SEARCH_DIRS]= empty_dir_path
        create_vectorstore(config)
