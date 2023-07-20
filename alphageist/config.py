from __future__ import annotations
from typing import Optional
import logging
import json
import copy
import os
from pathlib import Path
from platformdirs import user_config_dir
from .constant import APP_NAME, AUTHOR
from alphageist import state
from alphageist import errors
from alphageist import constant
from alphageist import util

logger = logging.getLogger(constant.LOGGER_NAME)


LLM_MODEL_NAME = "LLM_MODEL_NAME" 
LLM_TEMPERATURE = "LLM_TEMPERATURE"
API_KEY_OPEN_AI = "API_KEY_OPEN_AI"
VECTORDB_DIR = "VECTOR_DB_PATH" # The directory in which the DB is stored
SEARCH_DIRS = "SEARCH_DIRS"
LOG_LEVEL = "LOG_LEVEL"

REQUIRED_KEYS = {API_KEY_OPEN_AI, SEARCH_DIRS, VECTORDB_DIR}
class Config(dict):
    def _assert_has_required_keys(self):
        """Checks that the keys exist and that they have defined values"""
        missing_keys = REQUIRED_KEYS - set(self.keys())
        if missing_keys:
            raise errors.MissingConfigComponentsError(missing_keys) 
        missing_values = {key for key in REQUIRED_KEYS if not self[key]}
        if missing_values:
            raise errors.MissingConfigValueError(missing_values)

    def _assert_valid_values(self):
        """Checks that keys have valid values"""
        for key in self.keys():
            if key == LOG_LEVEL:
                allowed_values = ",".join({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
                if not self[key] in allowed_values:
                    raise errors.ConfigValueError(key, self[key], allowed_values)

    def check(self) -> None:
        self._assert_has_required_keys()
        self._assert_valid_values()
        
    def deepcopy(self)->Config:
        return Config(copy.deepcopy(self))

def get_default_config(ensure_exists: bool = True) -> Config:
    # Create a default config file
    DEFAULT_CONFIG = Config({
        LLM_MODEL_NAME: "gpt-4",
        LLM_TEMPERATURE: 0.0,
        API_KEY_OPEN_AI: "",
        VECTORDB_DIR: get_vectorDB_file_path(),
        SEARCH_DIRS: "",
        LOG_LEVEL: "INFO"
    })
    return DEFAULT_CONFIG

def bar():
    return user_config_dir()

def get_config_file_path(ensure_exists: bool = True) -> Path:
    # Use the user_config_dir function to get the directory path
    config_dir = user_config_dir(APP_NAME, AUTHOR, ensure_exists=ensure_exists)
    # Define your config file path
    return Path(config_dir) / "config.json"

def get_vectorDB_file_path(ensure_exists: bool = True) -> str:
    # Use the user_config_dir function to get the directory path
    vectorDB_dir = user_config_dir(APP_NAME, AUTHOR, ensure_exists=ensure_exists)

    # Define your config file path
    return os.path.join(vectorDB_dir, "vectorDatabase")

def save_config(config_file: Path, config: Config):
    logger.info(f"Saving config to {config_file}")
    with open(config_file, 'w') as f:
        f.write(json.dumps(config, indent=4))

def load_config(config_file: Path, default_config:Optional[Config] = None) -> Config:
    if config_file.exists():
        logger.info(f"Loading config from {config_file}")
        with open(config_file, 'r') as f:
            loaded_config = Config(json.load(f))
        
        # Check if all keys in default config are in loaded config
        if default_config:
            for key in default_config:
                if key not in loaded_config:
                    loaded_config[key] = default_config[key]

        return loaded_config
    else:
        if default_config is not None:
            return default_config
        else:
            raise ValueError("config_file can not be non existant and default_config be None")

