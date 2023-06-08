import sys
import os

from PyQt6.QtWidgets import QApplication

from alphageist import config as cfg
from alphageist.alphageist import Alphageist
from .spotlight_search import SpotlightSearch

TEST_DATA_PATH = os.path.join("test", "data")


def get_config()->dict:
    cfg_file = cfg.get_config_file_path()
    return cfg.load_config(cfg_file, cfg.get_default_config())

def run():
    app = QApplication(sys.argv)
    config = get_config()

    spotlight_search = SpotlightSearch(Alphageist(config))
    spotlight_search.show()
    exit_code = app.exec()
    sys.exit(exit_code)
