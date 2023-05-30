import sys
import os

from PyQt6.QtWidgets import QApplication

from alphageist import config as cfg
from .spotlight_search import SpotlightSearch

TEST_DATA_PATH = os.path.join("test", "data")


def get_config()->dict:
    cfg_file = cfg.get_config_file_path()
    return cfg.load_config(cfg_file, cfg.DEFAULT_CONFIG)

def run():
    app = QApplication(sys.argv)
    config = get_config()

    spotlight_search = SpotlightSearch(config)
    spotlight_search.show()
    sys.exit(app.exec())
