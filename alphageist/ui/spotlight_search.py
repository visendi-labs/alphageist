import os
import shutil
import re
import threading
import logging
import platform

from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QMetaObject, pyqtSlot, QSize
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QTextBrowser, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtWidgets import QPushButton, QLabel, QInputDialog, QDialog, QFormLayout, QStackedLayout, QLineEdit, QMenu, QFileDialog, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont, QPixmap, QAction, QIcon
import chromadb
import openai

from alphageist.query import get_sources_from_answer
from alphageist.vectorstore import create_vectorstore, vectorstore_exists, load_vectorstore
from alphageist.callbackhandler import CustomStreamHandler
from alphageist import state
from alphageist import errors
from alphageist import constant
from alphageist.alphageist import Alphageist
from alphageist.ui import util
from langchain.vectorstores.base import VectorStore
from langchain.schema import LLMResult

from .constant import ASSETS_DIRECTORY
from .constant import COLOR
from .constant import DESIGN
from .settings_dialog import SettingsDialog
import alphageist.config as cfg

logger = logging.getLogger(constant.LOGGER_NAME)

_icon_by_filetype = {
    ".txt": "txt.png",
    ".pdf": "pdf.png",
    ".csv": "csv.png",
    ".py": "python.png",
    ".go": "golang.png",
    ".pptx": "pptx.png",
    ".docx": "word.png",
    ".xlsx": "excel.png",
    ".xls": "excel.png",
    "default": "default_file.png"
}


def _get_image_path_by_filename(filename: str) -> str:
    _, file_extension = os.path.splitext(filename)
    return _icon_by_filetype.get(file_extension, _icon_by_filetype["default"])


RES_WIN_PREFIX = f"""
<style>
    body {{
         font-size: 16px;
    }}
    a {{
        color: white;
    }}
    a:hover {{
        color: #dddddd;
    }}
    a:visited {{
        color: #aaaaaa;
    }}
</style>
<body> 
"""
RES_WIN_POSTFIX = "</body>"


class ResultWindow(QTextBrowser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prevents ext. and local links from opening in search results window
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.setStyleSheet(
            f"""
            QTextBrowser {{
            background-color: {COLOR.GRAPHITE_DUST};
            border: 0px solid {COLOR.GRAPHITE_DUST};
            border-radius: 10px;
            color: {COLOR.WHITE};
            }}
            """
        )


class SpotlightSearch(QWidget):

    alphageist: Alphageist
    vectorstore: VectorStore

    error_msg: str # Displayed in search bar
    
    # Signals
    update_search_results_signal = pyqtSignal(str)
    setSearchResultVisible_signal = pyqtSignal(bool)
    adjustWindowSize_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.mpos = QPoint()
        self.settings_open = False
        self.settings_dialog = None
        self.error_msg = ""

        # Set up the user interface
        self.init_ui()

        # Set up the timer for checking focus
        self.check_focus_timer = QTimer(self)
        self.check_focus_timer.timeout.connect(self.check_focus)
        self.check_focus_timer.start(500)

        self.setFocus()  # Sets focus so the program wont shutdown

        # Set up the callback functionality making streaming possible
        self.init_callback()

        # Signals for toggling search result
        self.setSearchResultVisible_signal.connect(
            self.setSearchResultsVisible)
        self.adjustWindowSize_signal.connect(self.adjust_window_size)

        self.alphageist = Alphageist()
        self.alphageist.subscribe_to_statechange(self.on_statechange)
        self.alphageist.load_config()
    
    def init_callback(self):
        self.raw_response = []
        self.callback = CustomStreamHandler(
            self.on_llm_new_token, self.on_llm_end)
        self.muted = False
        self.update_search_results_signal.connect(self.update_search_results)

    @pyqtSlot(bool)
    def setSearchResultsVisible(self, visible: bool):
        self.search_results.setVisible(visible)

    @pyqtSlot(str)
    def update_search_results(self, text: str):
        self.search_results.setHtml(RES_WIN_PREFIX + text + RES_WIN_POSTFIX)
        self.search_results.setVisible(True)
        self.adjust_window_size()

    def _handle_error_state(self):
        exception = self.alphageist.exception
        if isinstance(exception, openai.error.AuthenticationError):
            self.set_search_bar_error_message("Invalid API Key")
        elif isinstance(exception, errors.MissingConfigValueError):
            self.set_search_bar_error_message(f"← Open settings...")
        elif isinstance(exception, chromadb.errors.NoIndexException):
            self.set_search_bar_error_message("Index broken")
        elif isinstance(exception, Exception):
            self.set_search_bar_error_message("Unkown error: Check error log")
            logger.exception("Got a unhandled exception in alghageist")
        else:
            logger.error("Trying to handle error but no exception exist")

    def on_statechange(self, old_state, new_state):
        if new_state is state.NEW:
            self.set_search_bar_disabled()
            self.alphageist.load_config()
        if new_state is state.CONFIGURED:
            self.set_search_bar_disabled()
            self.alphageist.start_init_vectorstore()
        if new_state is state.LOADING_VECTORSTORE:
            self.set_search_bar_disabled("Loading vectorstore...")
        if new_state is state.STANDBY:
            self.set_search_bar_stand_by()
        if new_state is state.QUERYING:
            self.set_search_bar_disabled()
        if new_state is state.ERROR:
            self._handle_error_state()            

    def on_llm_new_token(self, token: str, **kwargs):
        if self.muted:
            return
        if token == "OURCES" and self.raw_response[-1] == "S":
            self.muted = True
            self.raw_response.pop()
            self.update_search_results_signal.emit(''.join(self.raw_response))
        else:
            self.raw_response.append(token)
        response: str = ''.join(self.raw_response).replace('\n', '<br>')

        self.update_search_results_signal.emit(response)
        QMetaObject.invokeMethod(self, "update_search_results_signal",
                                 QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, response))

        self.setSearchResultVisible_signal.emit(True)
        self.adjustWindowSize_signal.emit()

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        answer = response.generations[0][0].text
        sources: list[str] = get_sources_from_answer(answer)

        # Append sources to the search result text
        search_result_text = ''.join(self.raw_response).replace('\n', '<br>')
        if sources[0] != "" and sources[0] != "N/A":
            search_result_text += "<br><br>Sources:"
            search_result_text += "<table>"
            for source in sources:
                icon_path = util.resource_path(os.path.join(
                    ASSETS_DIRECTORY, _get_image_path_by_filename(source)))
                search_result_text += f"""<tr>
                <td style='padding-right: 4px;'>
                <img src='{icon_path}' style='vertical-align: middle;' />
                </td>
                <td>
                <a href='{source.strip()}'>{source.strip()}</a>
                </td>
                </tr>"""
            search_result_text += "</table>"
        self.update_search_results_signal.emit(search_result_text)
        QMetaObject.invokeMethod(self, "update_search_results_signal",
                                 QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, search_result_text))
        self.muted = False
        self.raw_response = []

    def set_search_bar_error_frame(self, val: bool):
        if val:
            util.change_stylesheet_property(
                self.search_bar, "border", f"2px solid {COLOR.SUNSET_RED}")
        else:
            util.change_stylesheet_property(
                self.search_bar, "border", f"0px solid {COLOR.SUNSET_RED}")

    def set_search_bar_error_message(self, message: str)->None:
        self.set_search_bar_error_frame(True)
        self.search_bar.setText("")
        self.search_bar.setPlaceholderText(message)
        self.search_bar.setEnabled(False)
        self.setFocus()

    def set_search_bar_stand_by(self)->None:
        self.set_search_bar_error_frame(False)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setEnabled(True)

    def set_search_bar_disabled(self, message: Optional[str] = None)->None:
        self.set_search_bar_error_frame(False)
        if message is not None:
            self.search_bar.setPlaceholderText(message)
        self.search_bar.setEnabled(False)
        self.setFocus()

    def init_ui(self):
        # Set window properties
        self.set_window_properties()
        self.setStyleSheet(f"""
            color: {COLOR.WHITE};
            font-family: {DESIGN.FONT_FAMILY};
        """)
        # Set up the user interface
        layout = QVBoxLayout()
        layout.addLayout(self.create_search_layout())
        # Create text browser to display search results
        self.create_search_results()
        layout.addWidget(self.search_results)
        # Set the layout for the widget
        self.setLayout(layout)
        # Add drop shadow effect
        self.add_shadow_effect()

    def set_window_properties(self):
        self.setMinimumSize(600, 100)
        self.setMaximumSize(600, 100)
        self.center()
        # Remove window frame and background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def create_search_layout(self):
        # Create a horizontal layout for search bar and logo
        search_layout = QHBoxLayout()
        search_layout.setSpacing(2)  # Set spacing between logo and search bar
        # Create logo label and load logo image
        self.create_logo_label()
        search_layout.addWidget(self.logo_label)
        # Create search bar and set properties
        self.create_search_bar()
        search_layout.addWidget(self.search_bar)
        return search_layout

    def create_logo_label(self):
        self.logo_label = QLabel(self)
        logo_path = util.resource_path(os.path.join(ASSETS_DIRECTORY, "logo2_45x45.png"))
        logo_pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(logo_pixmap.scaled(
            45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))  # Adjust logo size
        # Create context menu for logo_label
        self.logo_label.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.logo_label.customContextMenuRequested.connect(
            self.show_logo_context_menu)
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.show_settings)

    def create_search_bar(self):
        self.search_bar = QLineEdit(self)
        font = QFont()
        font.setPointSize(16)  # Set size font of search bar text
        self.search_bar.setFont(font)
        self.search_bar.setFixedHeight(42)  # Adjust the height of search bar
        # Set default text in Search bar
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setStyleSheet(f"""
            background-color: {COLOR.OBSIDIAN_SHADOW}; 
            border: 0px solid {COLOR.GRAPHITE_DUST};
                        color: {COLOR.WHITE};
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
        """)

        self.search_bar.returnPressed.connect(self.start_search)

    def create_search_results(self):
        self.search_results = ResultWindow()
        self.search_results.setVisible(False)  # Hide search result initially
        self.search_results.anchorClicked.connect(self.open_file_link)

    def add_shadow_effect(self):
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(20)
        self.shadow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow_effect)

    def center(self):
        """
        Centers the main window of the application on the screen.

        This method calculates the center position of the screen based on the
        screen geometry and the window geometry. It then moves the window to
        that position.
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) / 2
        y = (screen_geometry.height() - window_geometry.height()) / 2
        self.move(int(x), int(y))

    def check_focus(self):
        # Shut down if user start focusing on something else
        if (not self.settings_open and
            not self.hasFocus() and
            not self.search_bar.hasFocus() and
                not self.search_results.hasFocus()):
            self.close()

    
    def start_search(self):
        query_string = self.search_bar.text()
        if not query_string:
            self.search_results.setVisible(False)
            self.adjust_window_size()
            return
        try:
            self.alphageist.start_search(query_string, callbacks=[self.callback])
        except errors.MissingConfigError:
            self.set_search_bar_error_message("No config loaded :/")
        except errors.MissingVectorstoreError:
            self.set_search_bar_error_message("No vectorstore loaded :/")
        except ValueError:
            logger.warning("Tried to start query with empty query string")    
        except errors.InvalidStateError as e:
            logger.exception(e)
        except Exception as e:
            self.set_search_bar_error_message("Ops, something went wrong. Check logs for more info")
            logger.exception(e)
        else:
            logger.info(f"starting search for: {query_string}")

    def show_settings(self):
        # If the settings dialog already exists, show it and don't create a new
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self.alphageist.config)
            self.settings_dialog.opened.connect(self.settings_opened)
            self.settings_dialog.closed.connect(self.settings_closed)
        self.settings_dialog.show()

    def show_logo_context_menu(self, position):
        context_menu = QMenu(self)
        context_menu.addAction(self.settings_action)
        context_menu.exec(self.logo_label.mapToGlobal(position))

    def open_file_link(self, url: str) -> None:
        filepath = url.path()
        # For Windows
        if platform.system() == 'Windows':
            # Open file, change to: os.startfile(os.path.dirname(filepath)) to instead open folder
            os.startfile(filepath)
        # For MacOS
        elif platform.system() == 'Darwin':
            # Open file, change to: os.system('open -R "{}"'.format(filepath)) to instead open folder
            os.system('open "{}"'.format(filepath))
        # Unsupported platform
        else:
            # Replace with correct error handling process
            print("Platform not supported.")

    def settings_opened(self):
        self.settings_open = True

    def settings_closed(self, config_changed: bool):
        self.settings_open = False
        if config_changed:
           self.alphageist.on_config_changed() 

    @pyqtSlot()
    def adjust_window_size(self):
        if self.search_results.isVisible():
            self.setMinimumSize(600, 400)
            self.setMaximumSize(600, 400)
        else:
            self.setMinimumSize(600, 100)
            self.setMaximumSize(600, 100)

    def mousePressEvent(self, event):
        self.mpos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        # Enable user to drag around serach bar on screen
        diff = event.globalPosition().toPoint() - self.mpos
        newpos = self.pos() + diff
        self.move(newpos)
        self.mpos = event.globalPosition().toPoint()
