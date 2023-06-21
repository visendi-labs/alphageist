from alphageist.ui import gui
from alphageist import errors
from alphageist import constant
from dotenv import load_dotenv
from alphageist.constant import APP_NAME, AUTHOR
from platformdirs import user_config_dir
import logging
import os

def get_log_file_path(ensure_exists: bool = True) -> str:
    # Use the user_config_dir function to get the directory path
    log_file_dir = user_config_dir(APP_NAME, AUTHOR, ensure_exists=ensure_exists)

    return os.path.join(log_file_dir, "logfile.log")

def setup_logging():
    FORMAT = "%(asctime)s %(filename)s:%(lineno)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.WARNING,
                    format=FORMAT)
    logger = logging.getLogger(constant.LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Create handlers
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    c_format = logging.Formatter(FORMAT)
    c_handler.setFormatter(c_format)

    # Create file handler which logs even debug messages
    f_handler = logging.FileHandler(get_log_file_path(), mode="w")
    f_handler.setLevel(logging.INFO)
    f_format = logging.Formatter(FORMAT)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

def main():
    setup_logging()
    gui.run()


if __name__ == "__main__":
    main()
else:
    raise errors.ForbiddenImportError("this file is not meant to be imported")
