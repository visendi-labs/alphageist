from alphageist.ui import gui
from dotenv import load_dotenv
import logging


class ForbiddenImportError(Exception):
    pass


def main():
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    gui.run()


if __name__ == "__main__":
    main()
else:
    raise ForbiddenImportError("this file is not meant to be imported")
