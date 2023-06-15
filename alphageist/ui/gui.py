import sys
import os

from PyQt6.QtWidgets import QApplication

from alphageist import config as cfg
from alphageist import vectorstore
from alphageist.alphageist import Alphageist
from .spotlight_search import SpotlightSearch

TEST_DATA_PATH = os.path.join("test", "data")

def run():
    app = QApplication(sys.argv)

    spotlight_search = SpotlightSearch()
    spotlight_search.show()
    exit_code = app.exec()
    sys.exit(exit_code)
