import logging
import json
import os
from platformdirs import user_config_dir
from .constant import APP_NAME, AUTHOR

API_KEY_OPEN_AI = "API_KEY_OPEN_AI"
VECTORDB_DIR = "VECTOR_DB_PATH" # The directory in which the DB is stored
SEARCH_DIRS = "SEARCH_DIRS"

def get_default_config(ensure_exists: bool = True) -> dict:
    # Create a default config file
    DEFAULT_CONFIG = {
        API_KEY_OPEN_AI: "",
        VECTORDB_DIR: get_vectorDB_file_path(),
        SEARCH_DIRS: ""
    }
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
    logging.info(f"Saving config to {config_file}")
    with open(config_file, 'w') as f:
        f.write(json.dumps(config))

def load_config(config_file: str, default_config: dict) -> dict:
    if os.path.exists(config_file):
        logging.info(f"Loading config from {config_file}")
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        
        # Check if all keys in default config are in loaded config
        for key in default_config:
            if key not in loaded_config:
                loaded_config[key] = default_config[key]

        return loaded_config
    else:
        return default_config  # if no config exists, return default

def has_necessary_components(config: dict)-> bool:
    required_keys = [API_KEY_OPEN_AI, SEARCH_DIRS, VECTORDB_DIR]
    for key in required_keys:
        if not key in config.keys():
            return False
    for key in required_keys:
        if not isinstance(config[key], str):
            raise ValueError(f"Value for key '{key}' must be a string")
        if config[key].strip() == "":
            return False
    return True