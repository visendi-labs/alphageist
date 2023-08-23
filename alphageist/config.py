from __future__ import annotations
from typing import (
    Optional, 
    Any,
)
import logging
import json
import copy
from pathlib import Path
from alphageist import (
    state,
    errors,
    constant,
    util,
)

logger = logging.getLogger(constant.LOGGER_NAME)


LLM_MODEL_NAME = "LLM_MODEL_NAME" 
LLM_TEMPERATURE = "LLM_TEMPERATURE"
API_KEY_OPEN_AI = "API_KEY_OPEN_AI"
VECTORDB_DIR = "VECTOR_DB_PATH" # The directory in which the DB is stored
SEARCH_DIRS = "SEARCH_DIRS"
LOG_LEVEL = "LOG_LEVEL"

REQUIRED_KEYS = {API_KEY_OPEN_AI, SEARCH_DIRS, VECTORDB_DIR}
class Config(dict[str, Any]):
    def __init__(self, *args, **kwargs):
        super().__init__()
        for key, value in dict(*args, **kwargs).items():
            self.__setitem__(key, value)

    def __setitem__(self, key, value):
        logger.debug(f"Updating config (in memory): {key} -> {value if key != API_KEY_OPEN_AI else 'sk-***'}")
        # Convert Paths to string in order to avoid json serialization problem on some win systems
        if isinstance(value, Path):
            value = str(value)
        super().__setitem__(key, value)
        
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
        VECTORDB_DIR: str(constant.VECTOR_DB_DIR),
        SEARCH_DIRS: "",
        LOG_LEVEL: "INFO"
    })
    return DEFAULT_CONFIG

def save_config(config_file: Path, config: Config):
    logger.info(f"Saving config to {config_file}")
    try:
        with open(config_file, 'w') as f:
            f.write(json.dumps(config, indent=4))
    except Exception as e:
        logger.exception("Was not able to save config")
        raise e
    else:
        logger.debug("Config saved successfully")

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

