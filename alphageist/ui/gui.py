import sys
import os

from PyQt6.QtWidgets import QApplication

from .spotlight_search import SpotlightSearch

TEST_DATA_PATH = os.path.join("test", "data")


def run():
    app = QApplication(sys.argv)
    spotlight_search = SpotlightSearch(TEST_DATA_PATH)
    spotlight_search.show()
    sys.exit(app.exec())
