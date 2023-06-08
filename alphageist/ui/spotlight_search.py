import os
import shutil
import re
import threading
import logging
import platform

from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QMetaObject, pyqtSlot, QSize
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QTextBrowser, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtWidgets import QPushButton, QLabel, QInputDialog, QDialog, QFormLayout, QStackedLayout, QLineEdit, QMenu, QFileDialog, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont, QPixmap, QAction, QIcon
import chromadb
import openai

from alphageist.query import query_vectorstore
from alphageist.query import get_sources_from_answer
from alphageist.vectorstore import create_vectorstore, vectorstore_exists, load_vectorstore
from alphageist.callbackhandler import CustomStreamHandler
from alphageist import state
from alphageist.alphageist import Alphageist
from alphageist.ui import util
from langchain.vectorstores.base import VectorStore
from langchain.schema import LLMResult

from .constant import ASSETS_DIRECTORY
from .constant import COLOR
from .constant import DESIGN
from .settings_dialog import SettingsDialog
import alphageist.config as cfg

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

    def __init__(self, alphagesist: Alphageist):
        super().__init__()
        self.alphageist = alphagesist

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

        # Set up the timer for checking if search-bar should be activated
        self.searchbar_status_timer = QTimer(self)
        self.searchbar_status_timer.timeout.connect(
            self._update_searchbar_status)
        self.searchbar_status_timer.start(100)
        self.setFocus()  # Sets focus so the program wont shutdown

        # Set up the callback functionality making streaming possible
        self.init_callback()

        # Signals for toggling search result
        self.setSearchResultVisible_signal.connect(
            self.setSearchResultsVisible)
        self.adjustWindowSize_signal.connect(self.adjust_window_size)

    def init_vectorstore(self):
        # Load vectorstore on main thread, create on separate
        if vectorstore_exists(self.alphageist.config[cfg.VECTORDB_DIR]):
            self.vectorstore = load_vectorstore(self.alphageist.config)
            self.alphageist.vectorstore_state = state.LOADED
        else:
            vectorstore_loading_thread = threading.Thread(
                target=self._create_vectorstore)
            vectorstore_loading_thread.daemon = True
            vectorstore_loading_thread.start()

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

    def _update_searchbar_status(self):
        if not cfg.has_necessary_components(self.alphageist.config):
            self.search_bar.setPlaceholderText(
                "← Open settings by right clicking on the logo...")
            self.search_bar.setEnabled(False)
            self.set_search_bar_error_frame(True)
            return

        if self.alphageist.vectorstore_state == state.ERROR:
            errtxt = self.error_msg if self.error_msg else "Error loading vectorstore DB. Check logs for more info."
            self.search_bar.setText("")
            self.search_bar.setEnabled(False)
            self.setFocus()
            self.search_bar.setPlaceholderText(errtxt)
            self.set_search_bar_error_frame(True)
            self.search_results.setVisible(False)
            self.adjust_window_size()
            return

        if self.alphageist.vectorstore_state == state.NOT_LOADED:
            self.search_results.setVisible(False)
            self.adjust_window_size()
            self.init_vectorstore()
            self.setFocus()
            return

        if self.alphageist.vectorstore_state == state.LOADING:
            self.search_bar.setText("")
            self.search_bar.setPlaceholderText("Loading vectorstore...")
            self.set_search_bar_error_frame(False)
            self.search_bar.setEnabled(False)
            self.setFocus()
            return

        if self.alphageist.query_state == state.ERROR:
            self.search_bar.setText("")
            errtxt = self.error_msg if self.error_msg else "Error querying. Check logs for more info."
            self.search_bar.setPlaceholderText(errtxt)
            self.set_search_bar_error_frame(True)
            self.search_bar.setEnabled(False)
            self.adjust_window_size()
            self.setFocus()
            self.search_results.setVisible(False)
            return

        self.set_search_bar_error_frame(False)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setEnabled(True)

    def set_search_bar_error_frame(self, val: bool):
        if val:
            util.change_stylesheet_property(
                self.search_bar, "border", f"2px solid {COLOR.SUNSET_RED}")
        else:
            util.change_stylesheet_property(
                self.search_bar, "border", f"0px solid {COLOR.SUNSET_RED}")

    def _create_vectorstore(self):
        self.alphageist.vectorstore_state = state.LOADING
        try:
            self.vectorstore = create_vectorstore(self.alphageist.config)
        except openai.error.AuthenticationError: 
            self.error_msg = "Invalid OpenAI API Key"
        except Exception as e:
            self.error_msg = "Unknown error: check logs"
            logging.exception(f"Unable to create vectorstore: {str(e)}")
            self.alphageist.vectorstore_state = state.ERROR
        else:
            logging.info("Vectorstore successfully created")
            self.alphageist.vectorstore_state = state.LOADED

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

        self.search_bar.returnPressed.connect(self.search)

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

    def _search(self, query: str):
        # Runs on separate thread
        self.alphageist.query_state = state.QUERYING
        try:
            res = query_vectorstore(
                self.vectorstore, query, self.alphageist.config, callbacks=[self.callback])
        except chromadb.errors.NoIndexException as e:
            # I think this happens if the db is not saved properly
            logging.exception(f"INDEX BROEKN: {str(e)}")
            self.alphageist.vectorstore_state = state.ERROR
            self.alphageist.query_state = state.ERROR
        except NotImplementedError as e:
            self.error_msg = "NOT IMPLEMENTED"
            self.alphageist.query_state = state.ERROR
        except openai.error.AuthenticationError as e:
            self.error_msg = "Error: Invalid OpenAI API Key"
            self.alphageist.query_state = state.ERROR
        except Exception as e:
            logging.exception(f"Error querying: {str(e)}")
            self.alphageist.query_state = state.ERROR
        else:
            logging.info(f"Search result: {res}")
            self.alphageist.query_state = state.STANDBY

    def search(self):
        if not self.search_bar.text():
            self.search_results.setVisible(False)
            self.adjust_window_size()
            return
        query_string = self.search_bar.text()
        query_thread = threading.Thread(
            target=self._search, args=(query_string,))
        query_thread.daemon = True
        logging.info(f"starting search for: {query_string}")
        query_thread.start()

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
            self.alphageist.vectorstore_state = state.NOT_LOADED
            if os.path.exists(self.alphageist.config[cfg.VECTORDB_DIR]):
                shutil.rmtree(self.alphageist.config[cfg.VECTORDB_DIR])

            self.alphageist.query_state = state.STANDBY

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
