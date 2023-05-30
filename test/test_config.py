
import json
from os import path
import pytest
from unittest.mock import mock_open, patch

from alphageist.config import save_config
from alphageist.config import load_config
from alphageist.config import has_necessary_components
import alphageist.config as cfg

TEST_FILE_PATH ="abccj"

TEST_DEFAULT_CONFIG = {'key': 'default_value'}  

test_data = path.join("test", "data")
test_cfg = {cfg.API_KEY_OPEN_AI: "abc123",
            cfg.VECTORDB_DIR: ".",
            cfg.SEARCH_DIRS: test_data}

def test_save_settings_config_is_saved():
    settings = {'key': 'value'}
    m = mock_open()
    with patch('alphageist.config.open', m, create=True):
        save_config(TEST_FILE_PATH, settings)

    handle = m()
    handle.write.assert_called_once_with(json.dumps(settings))


def test_load_settings_config_is_loaded():
    settings = {'key': 'value'}
    m = mock_open(read_data=json.dumps(settings))
    with patch('os.path.exists', return_value=True):  # Mock os.path.exists to return True
        with patch('builtins.open', m, create=True):
            result = load_config('filepath', TEST_DEFAULT_CONFIG)
    assert result == settings

def test_load_settings_file_not_found():
    m = mock_open()
    m.side_effect = FileNotFoundError
    with patch('alphageist.config.open', m, create=True):
        with patch('os.path.exists', return_value=False):  
            result = load_config(TEST_FILE_PATH, TEST_DEFAULT_CONFIG)
    assert result == TEST_DEFAULT_CONFIG

def test_load_settings_missing_keys_are_filled_from_default():
    partial_settings = {'key1': 'value1'}  # Assume 'key2' is missing and it's in the default config
    default_config = {'key1': 'default1', 'key2': 'default2'}
    expected_result = {'key1': 'value1', 'key2': 'default2'}

    m = mock_open(read_data=json.dumps(partial_settings))
    with patch('os.path.exists', return_value=True):  # Mock os.path.exists to return True
        with patch('builtins.open', m, create=True):
            result = load_config('filepath', default_config)
    assert result == expected_result

def test_has_necessary_components():
    # Test with all required components present and correct
    
    assert has_necessary_components(test_cfg) == True

    # Test with a missing key
    config = {
        cfg.SEARCH_DIRS: "/example/path"
    }
    assert has_necessary_components(config) == False

    # Test with an empty string value
    config = {
        cfg.API_KEY_OPEN_AI: "",
        cfg.SEARCH_DIRS: "/example/path"
    }
    assert has_necessary_components(config) == False


    # Test with all keys present but one value is whitespace only
    config = {
        cfg.API_KEY_OPEN_AI: "   ",
        cfg.SEARCH_DIRS: "/example/path"
    }
    assert has_necessary_components(config) == False