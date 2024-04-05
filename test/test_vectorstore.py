from os import path
from typing import List
import pytest
from unittest.mock import MagicMock

from random import random

from langchain.embeddings.base import Embeddings

from alphageist.vectorstore import VectorStore
from alphageist.vectorstore import get_embeddings
from alphageist import errors
from alphageist import config as cfg
from alphageist import state
from alphageist import vectorstore

from test.test_config import get_test_cfg_valid

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

empty_dir_path = path.join("test", "data", "empty_folder")

test_cfg_with_api_key = {cfg.API_KEY_OPEN_AI: "abc123"}

class MockEmbedding(Embeddings):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        embeddings = []
        for text in texts:
            v = self.embed_query(text)
            embeddings.append(v)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        return [random() for _ in range(10)] 

def test_vectorstore_first_state_is_new():
    v = VectorStore()
    assert v.state is state.NEW

@pytest.mark.parametrize("inval_state", {state.ERROR, state.LOADED, state.LOADING})
def test_start_init_vectorstore_incorrect_state(inval_state:state.State):
    v = VectorStore()
    v.state = inval_state
    with pytest.raises(errors.InvalidStateError):
        v.start_init_vectorstore(get_test_cfg_valid())

def test_start_init_vectorstore_clean_state(tmp_path):
    config = get_test_cfg_valid(tmp_path)

    v = VectorStore()
    v.start_init_vectorstore(config, emb = MockEmbedding())

    assert v.state == state.LOADING

    v._thread.join()

    assert v.state == state.LOADED
    assert path.exists(config[cfg.VECTORDB_DIR]) == True, "Expected vector DB directory to exist, but it does not"
    assert v.is_created() == True, "Expected vectorstore to be created and populated, but it is not"
    assert v.store.client.count(collection_name=vectorstore.COLLECTION_NAME).count > 0

def test_start_init_vectorstore_already_created(tmp_path):
    config = get_test_cfg_valid(tmp_path)

    v = VectorStore()
    v.start_init_vectorstore(config, emb = MockEmbedding())
    v._thread.join()

    del v.store.client
    v = VectorStore()
    v.start_init_vectorstore(config, emb = MockEmbedding())

    assert v._thread is None, "Threading is used for createing so there should be no thred"
    assert v.state == state.LOADED
    assert path.exists(config[cfg.VECTORDB_DIR]) == True, "Expected vector DB directory to exist, but it does not"
    assert v.is_created() == True, "Expected vectorstore to be created and populated, but it is not"
    assert v.store.client.count(collection_name=vectorstore.COLLECTION_NAME).count > 0

def test_start_init_vectorstore_empty_search_dir(tmp_path):
    config = get_test_cfg_valid(tmp_path)
    config[cfg.SEARCH_DIRS]= empty_dir_path
    v = VectorStore() 
    v.start_init_vectorstore(config, emb = MockEmbedding())
    v._thread.join()

    assert v.state == state.ERROR
    assert isinstance(v.exception, errors.NoSupportedFilesInDirectoryError)

def test_reset_mocked():
    v = VectorStore()
    mock_qdrantwrapper = MagicMock()
    v.store = mock_qdrantwrapper
    v.state = state.ERROR
    v.reset()

    mock_qdrantwrapper.client.delete_collection.called_once_with(collection_name=vectorstore.COLLECTION_NAME)
    assert v.state == state.NEW

def test_reset(tmp_path):
    config = get_test_cfg_valid(tmp_path)
    v = VectorStore()
    v.start_init_vectorstore(config, emb=MockEmbedding())
    v._thread.join()
    v.reset()

    assert v.is_created() == False

def test_reset_recreate(tmp_path):
    config = get_test_cfg_valid(tmp_path)
    v = VectorStore()
    v.start_init_vectorstore(config, emb=MockEmbedding())
    v._thread.join()
    v.reset()
    v.start_init_vectorstore(config, emb=MockEmbedding())
    v._thread.join()
    
    assert v.state == state.LOADED
    assert v.store.client.count(collection_name=vectorstore.COLLECTION_NAME).count > 0

def test_is_created_no_collection():
    v = VectorStore()
    assert v.is_created() == False

def test_get_embeddings_correct_type():
    e = get_embeddings(test_cfg_with_api_key)
    assert isinstance(e, Embeddings)

@pytest.mark.parametrize("inval_state", {state.NEW, state.LOADING, state.ERROR})
def test_query_incrorect_state(inval_state:state.State):
    v = VectorStore()
    v.state = inval_state
    with pytest.raises(errors.InvalidStateError):
        v.query(get_test_cfg_valid(), "blabla")

