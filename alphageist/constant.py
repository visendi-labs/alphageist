import sys
from platformdirs import user_data_dir
import pathlib 

from tufup.utils.platform_specific import ON_MAC, ON_WINDOWS # type: ignore

APP_NAME = "VisendiSearch"
AUTHOR = "Visendi"
LOGGER_NAME = "Alphageist"

# Are we running in a PyInstaller bundle?
# https://pyinstaller.org/en/stable/runtime-information.html
FROZEN = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# Current module dir (when frozen this equals sys._MEIPASS)
# https://pyinstaller.org/en/stable/runtime-information.html#using-file
INSTALL_DIR = pathlib.Path(__file__).resolve().parent.parent
APP_EXE_PATH = INSTALL_DIR / "Visendi Search.exe"

APP_DATA_DIR = pathlib.Path(user_data_dir(APP_NAME, AUTHOR, ensure_exists=True))
CONFIG_PATH = APP_DATA_DIR / "config.json"
LOG_PATH = APP_DATA_DIR / "logfile.log"
VECTOR_DB_DIR = APP_DATA_DIR / "vectorDatabase"

UPDATE_CACHE_DIR = APP_DATA_DIR / 'update_cache' 
METADATA_DIR = UPDATE_CACHE_DIR / 'metadata'
TARGET_DIR = UPDATE_CACHE_DIR / 'targets'

if ON_WINDOWS:
    METADATA_BASE_URL = 'https://visendi-search-artifacts.s3.eu-north-1.amazonaws.com/windows/metadata/'
    TARGET_BASE_URL = 'https://visendi-search-artifacts.s3.eu-north-1.amazonaws.com/windows/targets/'
elif ON_MAC:
    METADATA_BASE_URL = 'https://visendi-search-artifacts.s3.eu-north-1.amazonaws.com/mac/metadata/'
    TARGET_BASE_URL = 'https://visendi-search-artifacts.s3.eu-north-1.amazonaws.com/mac/targets/'
else:
    raise NotImplementedError('Unsupported platform')

# Location of trusted root metadata file
TRUSTED_ROOT_SRC = INSTALL_DIR / 'root.json'
if not FROZEN:
    # for development, get the root metadata directly from local repo
    TRUSTED_ROOT_SRC = INSTALL_DIR / 'temp/repository/metadata/root.json'
TRUSTED_ROOT_DST = METADATA_DIR / 'root.json'
