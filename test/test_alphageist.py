import pytest
from unittest.mock import Mock, MagicMock, patch
from alphageist.alphageist import Alphageist
from alphageist.vectorstore import VectorStore
from alphageist import state
from alphageist import errors

import test.test_config as test_cfg

def get_mocked_configured_alphgeist(magicmock: MagicMock)->Alphageist:
    a = Alphageist()
    a.vectorstore = magicmock
    with patch("alphageist.alphageist.get_config") as mock_get_config:
        mock_get_config.return_value = test_cfg.test_cfg_valid
        a.load_config()
    return a

def get_mocked_standby_alphageist(magicmock: MagicMock)->Alphageist:
    a = get_mocked_configured_alphgeist(magicmock)
    a.start_init_vectorstore()
    a.finish_init_vectorstore()
    return a

def test_first_state_is_new():
    a = Alphageist()
    assert a.state is state.NEW

def test_load_config_valid_cfg():
    a = Alphageist()
    with patch("alphageist.alphageist.get_config") as mock_get_config:
        mock_get_config.return_value = test_cfg.test_cfg_valid
        a.load_config()
    assert a.state is state.CONFIGURED
    assert a.exception is None

def test_load_config_invalid_cfg_state_is_changed_to_error():
    a = Alphageist()
    with patch("alphageist.alphageist.get_config") as mock_get_config:
        mock_get_config.return_value = test_cfg.test_cfg_missing_api_key
        a.load_config()
    assert a.state is state.ERROR
    assert isinstance(a.exception, errors.MissingConfigComponentsError)

@patch("alphageist.alphageist.get_config", side_effect=Exception('This is an error message'))
def test_load_config_exception_fetching_config(mock_get_config):
    a = Alphageist()
    a.load_config()
    assert a.state is state.ERROR
    assert isinstance(a.exception, Exception)

def test_start_load_vectorstore_incorrect_state():
    a = Alphageist()
    with pytest.raises(errors.InvalidStateError):
        a.start_init_vectorstore()

def test_start_load_vectorstore():
    mock_vectorstore = MagicMock()
    a = get_mocked_configured_alphgeist(mock_vectorstore)

    a.start_init_vectorstore()

    mock_vectorstore.start_init_vectorstore.assert_called_once_with(a.config)
    assert a.state is state.LOADING_VECTORSTORE 

def test_finish_loading_vectorstore_incorrect_state():
    a = Alphageist()
    with pytest.raises(errors.InvalidStateError):
        a.finish_init_vectorstore()

def test_finish_loading_vectorstore():
    mock_vectorstore = MagicMock()
    a = get_mocked_configured_alphgeist(mock_vectorstore)
    a.start_init_vectorstore()

    a.finish_init_vectorstore()

    assert a.state is state.STANDBY

def test_start_search_incorrect_state():
    a = Alphageist()
    with pytest.raises(errors.InvalidStateError):
        a.start_search("hej")

def test_start_search_empty_search_string():
    mock_vectorstore = MagicMock()
    a = get_mocked_standby_alphageist(mock_vectorstore)
    with pytest.raises(ValueError):
        a.start_search("")

def test_start_search():
    mock_vectorstore = MagicMock()
    mock_callback_handler = MagicMock()
    a = get_mocked_standby_alphageist(mock_vectorstore)
    a.start_search("hej", [mock_callback_handler])

    mock_vectorstore.query.assert_called_once()
    assert a.state is state.QUERYING
    
def test_reset():
    mock_vectorstore = MagicMock()
    a = get_mocked_standby_alphageist(mock_vectorstore)
    a.reset()
    assert a.state is state.NEW
    assert a.exception is None
    assert isinstance(a.vectorstore, VectorStore)

def test_reset_incorrect_state():
    a = Alphageist()
    a.state = state.LOADING_VECTORSTORE
    with pytest.raises(errors.InvalidStateError):
        a.reset()

########################

# def test_state_subscription():
#     a = Alphageist(test_cfg, VectorStore())
#     callback_mock = Mock()

#     a.state = state.STANDBY
#     a.subscribe_to_statechange(callback_mock)
#     a.state = state.ERROR

#     callback_mock.assert_called_once_with(state.STANDBY, state.ERROR)
    
# def test_state_subscription_changed_to_same_state():
#     a = Alphageist(test_cfg, VectorStore())
#     callback_mock = Mock()

#     a.state = state.STANDBY
#     a.subscribe_to_statechange(callback_mock)
#     a.state = state.STANDBY

#     callback_mock.assert_not_called()


# def test_state_subscription_subscribe_twice():

#     a = Alphageist(test_cfg, VectorStore())
#     callback_mock = Mock()

#     a.state = state.STANDBY
#     a.subscribe_to_statechange(callback_mock)
#     a.subscribe_to_statechange(callback_mock)
#     a.state = state.ERROR

#     callback_mock.assert_called_once_with(state.STANDBY, state.ERROR)
    
# def test_state_subscription_unsubscribe_not_subscribing():

#     a = Alphageist(test_cfg, VectorStore())
#     callback_mock = Mock()
#     with pytest.raises(ValueError):
#         a.unsubscribe_to_statechange(callback_mock)
        
# def test_state_subscription_unsubscribe():

#     a = Alphageist(test_cfg, VectorStore())
#     callback_mock = Mock()
#     a.subscribe_to_statechange(callback_mock)
#     a.unsubscribe_to_statechange(callback_mock)
#     a.state = state.ERROR

#     callback_mock.assert_not_called()
