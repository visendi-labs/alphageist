
import json
from os import path
import pytest
from unittest.mock import mock_open, patch

from alphageist.config import save_config
from alphageist.config import load_config
from alphageist.config import Config
from alphageist import errors
import alphageist.config as cfg

TEST_FILE_PATH ="abccj"

TEST_DEFAULT_CONFIG = Config({'key': 'default_value'})

test_data = path.join("test", "data")
test_cfg_valid = Config({cfg.API_KEY_OPEN_AI: "abc123",
            cfg.VECTORDB_DIR: ".",
            cfg.SEARCH_DIRS: test_data})

test_cfg_missing_api_key = Config({cfg.VECTORDB_DIR: ".",
            cfg.SEARCH_DIRS: test_data})

def test_save_settings_config_is_saved():
    settings = {'key': 'value'}
    m = mock_open()
    with patch('alphageist.config.open', m, create=True):
        save_config(TEST_FILE_PATH, settings)

    handle = m()
    handle.write.assert_called_once_with(json.dumps(settings, indent=4))


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
    partial_settings = Config({'key1': 'value1'})  # Assume 'key2' is missing and it's in the default config
    default_config = Config({'key1': 'default1', 'key2': 'default2'})
    expected_result = Config({'key1': 'value1', 'key2': 'default2'})

    m = mock_open(read_data=json.dumps(partial_settings))
    with patch('os.path.exists', return_value=True):  # Mock os.path.exists to return True
        with patch('builtins.open', m, create=True):
            result = load_config('filepath', default_config)
    assert result == expected_result

def test_all_required_keys_present_with_values():
    config = Config({
        cfg.API_KEY_OPEN_AI: 'some_key',
        cfg.VECTORDB_DIR: 'some_path',
        cfg.SEARCH_DIRS: 'some_dirs',
    })
    # Should not raise any exception
    config._assert_has_required_keys()

def test_missing_required_key():
    config = Config({
        cfg.API_KEY_OPEN_AI: 'some_key',
        cfg.SEARCH_DIRS: 'some_dirs',
    })
    # Should raise MissingConfigComponentsError as VECTORDB_DIR is missing
    with pytest.raises(errors.MissingConfigComponentsError):
        config._assert_has_required_keys()

def test_empty_required_key_value():
    config = Config({
        cfg.API_KEY_OPEN_AI: 'some_key',
        cfg.VECTORDB_DIR: '',
        cfg.SEARCH_DIRS: 'some_dirs',
    })
    # Should raise MissingConfigValueError as VECTORDB_DIR is empty
    with pytest.raises(errors.MissingConfigValueError):
        config._assert_has_required_keys()

@pytest.mark.parametrize("key, value", [
    (cfg.LOG_LEVEL, "not a log level")
])
def test_invalid_value(key:str, value:str):
    config = test_cfg_valid
    config[key] = value
    with pytest.raises(errors.ConfigValueError) as e:
        config.check()

    assert e.value.key == key
    assert e.value.value == value
        
     