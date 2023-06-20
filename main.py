from alphageist.ui import gui
from alphageist import errors
from alphageist import constant
from dotenv import load_dotenv
import logging


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
    f_handler = logging.FileHandler('logfile.log')
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
