from typing import Optional
import json
from pathlib import Path
import pytest
from unittest.mock import mock_open, patch

from alphageist.config import save_config
from alphageist.config import load_config
from alphageist.config import Config
from alphageist import errors
import alphageist.config as cfg

TEST_FILE_PATH = Path("abccj")
TEST_DEFAULT_CONFIG = Config({'key': 'default_value'})

TEST_DATA_PATH = Path("test") / "data"
__test_cfg_valid = Config({cfg.API_KEY_OPEN_AI: "abc123",
                         cfg.VECTORDB_DIR: ".",
                         cfg.SEARCH_DIRS: TEST_DATA_PATH})

test_cfg_missing_api_key = Config({cfg.VECTORDB_DIR: ".",
            cfg.SEARCH_DIRS: TEST_DATA_PATH})

def get_test_cfg_valid(work_dir:Optional[str]=None)->Config:
    """Returns a deepcopy of a valid config. Vector DB dir will be set
       to work_dir if specified."""
    c = __test_cfg_valid.deepcopy()
    if work_dir is not None:
        c[cfg.VECTORDB_DIR] = work_dir
    return c

def test_save_settings_config_is_saved():
    settings = {'key': 'value'}
    m = mock_open()
    with patch('alphageist.config.open', m, create=True):
        save_config(TEST_FILE_PATH, settings)

    handle = m()
    handle.write.assert_called_once_with(json.dumps(settings, indent=4))

def test_all_required_keys_present_with_values():
    get_test_cfg_valid()._assert_has_required_keys()

@pytest.mark.parametrize("missing_key", cfg.REQUIRED_KEYS)
def test_missing_required_key(missing_key:str):
    config = get_test_cfg_valid()
    config.pop(missing_key)
    # Should raise MissingConfigComponentsError as VECTORDB_DIR is missing
    with pytest.raises(errors.MissingConfigComponentsError) as exec_info:
        config._assert_has_required_keys()
    
    assert missing_key in exec_info.value.missing_keys

@pytest.mark.parametrize("key", cfg.REQUIRED_KEYS)
def test_required_key_has_missing_value(key):
    config = get_test_cfg_valid() 
    config[key] = ""
    # Should raise MissingConfigValueError as VECTORDB_DIR is empty
    with pytest.raises(errors.MissingConfigValueError) as exec_info:
        config._assert_has_required_keys()
    
    assert key in exec_info.value.keys

@pytest.mark.parametrize("key, value", [
    (cfg.LOG_LEVEL, "not a log level"),
])
def test_invalid_value(key:str, value:str):
    config = get_test_cfg_valid()
    config[key] = value
    with pytest.raises(errors.ConfigValueError) as e:
        config.check()

    assert e.value.key == key
    assert e.value.value == value
        
     