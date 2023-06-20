import logging
import json
import os
from platformdirs import user_config_dir
from .constant import APP_NAME, AUTHOR
from alphageist import state
from alphageist import errors
from alphageist import constant

logger = logging.getLogger(constant.LOGGER_NAME)


LLM_MODEL_NAME = "LLM_MODEL_NAME" 
LLM_TEMPERATURE = "LLM_TEMPERATURE"
API_KEY_OPEN_AI = "API_KEY_OPEN_AI"
VECTORDB_DIR = "VECTOR_DB_PATH" # The directory in which the DB is stored
SEARCH_DIRS = "SEARCH_DIRS"

required_keys = {API_KEY_OPEN_AI, SEARCH_DIRS, VECTORDB_DIR}
class Config(dict):
    state: state.State
    def assert_has_required_keys(self) -> None:
        """Checks that the keys exist and that they have defined values"""
        missing_keys = required_keys - set(self.keys())
        if missing_keys:
            raise errors.MissingConfigComponentsError(missing_keys) 
        missing_values = {key for key in required_keys if not self[key]}
        if missing_values:
            raise errors.MissingConfigValueError(missing_values)

def get_default_config(ensure_exists: bool = True) -> Config:
    # Create a default config file
    DEFAULT_CONFIG = Config({
        LLM_MODEL_NAME: "gpt-4",
        LLM_TEMPERATURE: 0.0,
        API_KEY_OPEN_AI: "",
        VECTORDB_DIR: get_vectorDB_file_path(),
        SEARCH_DIRS: ""
    })
    return DEFAULT_CONFIG

def get_config_file_path(ensure_exists: bool = True) -> str:
    # Use the user_config_dir function to get the directory path
    config_dir = user_config_dir(APP_NAME, AUTHOR, ensure_exists=ensure_exists)

    # Define your config file path
    return os.path.join(config_dir, "config.json")

def get_vectorDB_file_path(ensure_exists: bool = True) -> str:
    # Use the user_config_dir function to get the directory path
    vectorDB_dir = user_config_dir(APP_NAME, AUTHOR, ensure_exists=ensure_exists)

    # Define your config file path
    return os.path.join(vectorDB_dir, "vectorDatabase")

def save_config(config_file: str, config: dict):
    logger.info(f"Saving config to {config_file}")
    with open(config_file, 'w') as f:
        f.write(json.dumps(config))

def load_config(config_file: str, default_config: Config) -> Config:
    if os.path.exists(config_file):
        logger.info(f"Loading config from {config_file}")
        with open(config_file, 'r') as f:
            loaded_config = Config(json.load(f))
        
        # Check if all keys in default config are in loaded config
        for key in default_config:
            if key not in loaded_config:
                loaded_config[key] = default_config[key]

        return loaded_config
    else:
        return default_config  # if no config exists, return default

