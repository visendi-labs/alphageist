from alphageist.ui import gui
from dotenv import load_dotenv


class ForbiddenImportError(Exception):
    pass


def main():
    load_dotenv()
    gui.run()


if __name__ == "__main__":
    main()
else:
    raise ForbiddenImportError("this file is not meant to be imported")
