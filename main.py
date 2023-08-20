import logging
import pathlib
import shutil
import os
from dotenv import load_dotenv
from platformdirs import user_config_dir

from tufup.client import Client # type: ignore
from tuf.api.exceptions import (
    DownloadHTTPError,
    ExpiredMetadataError,
)
from PyQt6.QtWidgets import QApplication

from alphageist import (
    errors,
    __version__,
    ui,
    constant
)
from alphageist.ui import (
    gui,
    update as ui_update
)

MODULE_DIR = pathlib.Path(__file__).resolve().parent

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
    f_handler = logging.FileHandler(constant.LOG_PATH, mode="w")
    f_handler.setLevel(logging.INFO)
    f_format = logging.Formatter(FORMAT)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger


CUSTOM_BATCH_TEMPLATE = """@echo off
{log_lines}
echo Moving app files...
robocopy "{src_dir}" "{dst_dir}" {robocopy_options}
echo Done.
echo Restarting app
start "" "{app_exe_path}"
{delete_self}
"""

def update():
    client = Client(
        app_name=constant.APP_NAME,
        app_install_dir=MODULE_DIR,
        current_version=__version__,
        metadata_dir=constant.METADATA_DIR,
        metadata_base_url=constant.METADATA_BASE_URL,
        target_dir=constant.TARGET_DIR,
        target_base_url=constant.TARGET_BASE_URL,
        refresh_required=True,
    )

    # Perform update
    try:
        updates = client.check_for_updates()
    except SystemExit:
        updates = None
        logger.warning(f"Was not able to check for new updates")
    except ExpiredMetadataError as e:
        updates = None
        logger.warning(f"Was not able to update: {str(e)}")
    except Exception as e:
        raise e

    if updates:
        logger.info(f"Downloading, applying the update and restarting app...")

        app = QApplication(sys.argv)
        upd_win = ui_update.UpdateWindow()
        upd_win.show()

        client.download_and_apply_update(
            # WARNING: Be very careful with purge_dst_dir=True, because this
            # will delete *EVERYTHING* inside the app_install_dir, except
            # paths specified in exclude_from_purge. So, only use
            # purge_dst_dir=True if you are certain that your app_install_dir
            # does not contain any unrelated content.
            progress_hook=upd_win.progress_hook,
            purge_dst_dir=False,
            skip_confirmation=True,
            exclude_from_purge=None,
            log_file_name='install.log',
            batch_template=CUSTOM_BATCH_TEMPLATE, 
            batch_template_extra_kwargs=dict(app_exe_path=constant.APP_EXE_PATH), 
        )
        exit_code = app.exec()

def main():
    logger.info(f"Starting Visendi Search version {__version__}")
    # Automatic updates are only enabled for windows for now
    if constant.ON_WINDOWS:
        # The app must ensure dirs exist
        for dir_path in [constant.INSTALL_DIR, constant.METADATA_DIR, constant.TARGET_DIR]:
            dir_path.mkdir(exist_ok=True, parents=True)

        # The app must be shipped with a trusted "root.json" metadata file,
        # which is created using the tufup.repo tools. The app must ensure
        # this file can be found in the specified metadata_dir. The root metadata
        # file lists all trusted keys and TUF roles.
        if not constant.TRUSTED_ROOT_DST.exists():
            shutil.copy(src=constant.TRUSTED_ROOT_SRC, dst=constant.TRUSTED_ROOT_DST)
            logger.info('Trusted root metadata copied to cache.')

        update()

    gui.run()


if __name__ == "__main__":
    logger = setup_logging()
    main()
