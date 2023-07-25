import os
import threading
import shutil
import re
import threading
import logging
import platform
import itertools

from typing import (
    Optional,
    Iterable
)

from PyQt6.QtCore import (
    Qt, 
    QTimer, 
    QPoint,
    QMetaObject, 
    pyqtSlot, 
    QSize, 
    QUrl
)
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication, 
    QWidget, 
    QFrame,
    QVBoxLayout, 
    QHBoxLayout, 
    QLineEdit, 
    QTextEdit, 
    QTextBrowser, 
    QLabel, 
    QGraphicsDropShadowEffect,
    QPushButton, 
    QLabel, 
    QInputDialog, 
    QDialog, 
    QFormLayout, 
    QStackedLayout, 
    QLineEdit, 
    QMenu, 
    QFileDialog, 
    QSpacerItem, 
    QSizePolicy
)
from PyQt6.QtGui import (
    QFont, 
    QPixmap, 
    QAction, 
    QIcon, 
    QCursor
)
import openai

from alphageist.query import get_sources_from_answer
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

class SearchBar(QLineEdit):
    def __init__(self):
        super().__init__()
        font = QFont()
        font.setPointSize(15)  # Set size font of search bar text
        self.setFont(font)

        self.setStyleSheet(f"""
            color: {COLOR.WHITE};
            border-radius: 0px;
        """)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        self.timer = QTimer()

    def setDisabled(self, disabled):
        # Disabling the line edit but not its child button
        super().setDisabled(disabled)
    
    @pyqtSlot(str)
    @util.force_main_thread(str)
    def setPlaceholderText(self, text:str)->None:
        """Stop any ongoing dynamic updating of placeholder and then update placeholder text"""
        self.timer.stop()
        try:
            self.timer.timeout.disconnect()
        except TypeError:
            pass 
        super().setPlaceholderText(text)

    @pyqtSlot(list, int)
    @util.force_main_thread(list, int)
    def set_alternating_placeholder_text(self, texts:Iterable[str], interval_ms:int)->None:
        cycler = itertools.cycle(texts)
        self.timer.timeout.connect(lambda: super(SearchBar,self).setPlaceholderText(next(cycler)))
        self.timer.start(interval_ms)

class OptionsButton(QPushButton):
    def __init__(self):
        super().__init__()
        icon_path = util.resource_path(os.path.join(ASSETS_DIRECTORY, "options_icon_21x21.png"))
        self.setIcon(QIcon(QPixmap(icon_path)))
        self.setFixedSize(DESIGN.BUTTON_OPTN_WIDTH, DESIGN.BUTTON_OPTN_HEIGHT)
        self.setStyleSheet(
            f"""
            QPushButton{{
                border: 0px solid white;
                border-radius: {DESIGN.BUTTON_OPTN_RADIUS}; 
                background-color: {COLOR.OBSIDIAN_SHADOW};
            }}
            QPushButton:hover{{
                background-color: {COLOR.GRAPHITE_DUST};
            }}
            """
        )
        self.create_context_menu()

    @pyqtSlot(bool)
    @util.force_main_thread(bool)
    def set_error_frame(self, val: bool):
        if val:
            util.change_stylesheet_property(
                self, "border", f"2px solid {COLOR.SUNSET_RED}")
        else:
            util.change_stylesheet_property(
                self, "border", f"0px solid {COLOR.SUNSET_RED}")


    def create_context_menu(self):
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.context_menu = QMenu(self)
        self.context_menu.setStyleSheet(f"""
            QMenu {{
                padding: 2px 2px 2px 2px;
                background-color: {COLOR.OBSIDIAN_SHADOW};
                border: 1px solid {COLOR.GRAPHITE_DUST};
                border-radius: 0px;
            }}

            QMenu::item {{
                padding: 2px 20px 2px 20px;
                border-radius: 5px;  
                color: {COLOR.MOONLIT_SNOW}; 
            }}
            
            QMenu::item:selected {{
                background-color: {COLOR.GRAPHITE_DUST};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.showContextMenu(event.pos())
        super().mousePressEvent(event)

    def showContextMenu(self, position):
        self.context_menu.exec(self.mapToGlobal(position))

class Logo(QLabel):
    def __init__(self):
        super().__init__()
        logo_path = util.resource_path(os.path.join(ASSETS_DIRECTORY, "logo2_45x45.png"))
        logo_pixmap = QPixmap(logo_path)
        self.setPixmap(logo_pixmap.scaled(
            45, 45, Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation))
        self.setStyleSheet(f"""
            background: {COLOR.GRAPHITE_DUST};
            border-top-left-radius: {DESIGN.ELEMENT_RADIUS};
            border-bottom-left-radius: {DESIGN.ELEMENT_RADIUS};
        """)

class SearchBarContainer(QFrame):
    """Contains searchbar and options button"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            background-color: {COLOR.OBSIDIAN_SHADOW}; 
            border-top-right-radius: {DESIGN.ELEMENT_RADIUS};
            border-bottom-right-radius: {DESIGN.ELEMENT_RADIUS};
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 6, 0) #TODO hot number, should be calculated
        self.search_bar = SearchBar()
        self.optn_btn = OptionsButton()
        layout.addWidget(self.search_bar, 1)
        layout.addWidget(self.optn_btn, 0)
        self.setLayout(layout)

class BarContainer(QFrame):
    """Contains the logo and the searchbar container"""
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.logo = Logo()
        self.search_bar_container = SearchBarContainer()
        layout.addWidget(self.logo)
        layout.addWidget(self.search_bar_container)
        self.setLayout(layout)
        self.setStyleSheet(f"""
            border: 0px solid white;
        """)

class ResultWindow(QTextBrowser):
    HTML = f"""
    <style>
        body {{
            font-size: {DESIGN.RESULT_WIN_FONT_SIZE};
        }}
        a {{
            color: {COLOR.WHITE};
        }}
    </style>
    <body> 
        %s
    </body>
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedHeight(DESIGN.RESULT_WIN_HEIGHT)

        # Prevents ext. and local links from opening in search results window
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: {DESIGN.RESULT_WIN_BG_COLOR};
                border: 1 solid {COLOR.STEEL_HAZE};
                border-radius: {DESIGN.ELEMENT_RADIUS};
                color: {COLOR.WHITE};
            }}
            """
        )
        self.document().setDocumentMargin(DESIGN.RESULT_WIN_TEXT_MARGIN)

    def set_text(self, text:str)->None:
        self.setHtml(self.HTML % text)

    
class SpotlightSearch(QWidget):

    alphageist: Alphageist
    vectorstore: VectorStore

    error_msg: str # Displayed in search bar
    
    def __init__(self):
        super().__init__()
        
        self.settings_open = False
        self.settings_dialog = None
        self.error_msg = ""

        self.init_ui()
        self.init_action_bindings()
        self.init_callback()

        self.alphageist = Alphageist()
        self.alphageist.subscribe_to_statechange(self.on_statechange)
        self.alphageist.load_config()

    def init_ui(self):
        self.set_window_properties()
        self.setWindowIcon(QIcon(os.path.join(ASSETS_DIRECTORY, "Visendi.ico")))

        self.setStyleSheet(f"""
            color: {COLOR.WHITE};
            font-family: {DESIGN.FONT_FAMILY};
        """)

        # Set up the user interface
        layout = QVBoxLayout()
        self.bar_container = BarContainer()
        self.create_result_window()
        layout.addWidget(self.bar_container)
        layout.addWidget(self.result_window)
        layout.addStretch()
        self.setLayout(layout)

        self.add_shadow_effect()

    def set_window_properties(self):
        self.setFixedWidth(DESIGN.PROGRAM_WIDTH)
        self.center()
        # Remove window frame and background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def init_action_bindings(self):
        # Options button drop down menu
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        close_action = QAction("Exit", self)
        close_action.triggered.connect(self.close)
        self.bar_container.search_bar_container.optn_btn.context_menu.addAction(settings_action)
        self.bar_container.search_bar_container.optn_btn.context_menu.addAction(close_action)

        # Hotkey for start search
        self.bar_container.search_bar_container.search_bar.returnPressed.connect(self.start_search)

    def init_callback(self):
        self.raw_response = []
        self.callback = CustomStreamHandler(
            self.on_llm_new_token, self.on_llm_end)
        self.muted = False

    @pyqtSlot(bool)
    @util.force_main_thread(bool)
    def setSearchResultsVisible(self, visible: bool):
        self.result_window.setVisible(visible)

    @pyqtSlot(str)
    @util.force_main_thread(str)
    def update_search_results(self, text: str):
        self.result_window.set_text(text)
        self.result_window.setVisible(True)

    def _handle_error_state(self):
        """This method is called from another thread"""
        exception = self.alphageist.exception
        if isinstance(exception, openai.error.AuthenticationError):
            self.set_search_bar_error_message("Invalid API Key")
        elif isinstance(exception, errors.MissingConfigValueError):
            self.set_search_bar_error_message(f"Open settings... →")
        elif isinstance(exception, errors.ConfigValueError):
            self.set_search_bar_error_message(f"Config error: '{exception.value}' is an invalid value for {exception.key}")
        elif isinstance(exception, errors.NoSupportedFilesInDirectoryError):
            self.set_search_bar_error_message("No supported files found in the search directory")
        elif isinstance(exception, Exception):
            self.set_search_bar_error_message("Unkown error: Check error log")
            logger.exception("Got a unhandled exception in alghageist")
        else:
            logger.error("Trying to handle error but no exception exist")

    def on_statechange(self, old_state:state.State, new_state:state.State):
        if new_state is state.NEW:
            self.set_search_bar_disabled()
            self.alphageist.load_config()
        if new_state is state.CONFIGURED:
            self.set_search_bar_disabled()
            self.alphageist.start_init_vectorstore()
        if new_state is state.LOADING_VECTORSTORE:
            self.set_search_bar_disabled()
            self.bar_container.search_bar_container.search_bar.setText("")
            self.bar_container.search_bar_container.search_bar.set_alternating_placeholder_text(
                ["Loading.", "Loading..", "Loading..."], 300)
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
            self.update_search_results(''.join(self.raw_response))
        else:
            self.raw_response.append(token)
        response: str = ''.join(self.raw_response).replace('\n', '<br>')
        self.update_search_results(response)

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
                search_result_text += f"""
                <tr>
                    <td style='padding-right: 4px;'>
                        <img src='{icon_path}' style='vertical-align: middle;' />
                    </td>
                    <td>
                        <a href='{source.strip()}'>{source.strip()}</a>
                    </td>
                </tr>"""
            search_result_text += "</table>"

        self.update_search_results(search_result_text)
        self.muted = False
        self.raw_response = []

    
    @pyqtSlot(str)
    @util.force_main_thread(str)
    def set_search_bar_error_message(self, message: str)->None:
        self.bar_container.search_bar_container.optn_btn.set_error_frame(True)
        self.bar_container.search_bar_container.search_bar.setText("")
        self.bar_container.search_bar_container.search_bar.setPlaceholderText(message)
        self.bar_container.search_bar_container.search_bar.setEnabled(False)

    @pyqtSlot()
    @util.force_main_thread()
    def set_search_bar_stand_by(self)->None:
        self.bar_container.search_bar_container.optn_btn.set_error_frame(False)
        self.bar_container.search_bar_container.search_bar.set_alternating_placeholder_text(
            util.stream_texts_incrementally([
                "What are our company's core values?", 
                "What's the efficiency of our GXB5 gearbox?",
                "Vad har Erik på säljavdelningen för telefonnummer?",
                "What was our last years net result?",
                "Who was accountant manager Q3 2009?",
                "What are our patents?"],
                repeat_full=50), 
                30)
        self.bar_container.search_bar_container.search_bar.setEnabled(True)

    @pyqtSlot(str)
    @util.force_main_thread()
    def set_search_bar_disabled(self)->None:
        self.bar_container.search_bar_container.optn_btn.set_error_frame(False)
        self.bar_container.search_bar_container.search_bar.setEnabled(False)
    
    def create_result_window(self):
        self.result_window = ResultWindow()
        self.result_window.setVisible(False)  # Hide search result initially
        self.result_window.anchorClicked.connect(util.open_file_link)

    def add_shadow_effect(self):
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(20)
        self.shadow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow_effect)

    @util.force_main_thread()
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

    def start_search(self):
        query_string = self.bar_container.search_bar_container.search_bar.text()
        if not query_string:
            self.result_window.setVisible(False)
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

    def settings_opened(self):
        self.settings_open = True

    def settings_closed(self, config_changed: bool):
        self.settings_open = False
        if config_changed:
           self.alphageist.on_config_changed() 

    def mousePressEvent(self, event):
        self.mpos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        # Enable user to drag around serach bar on screen
        diff = event.globalPosition().toPoint() - self.mpos
        newpos = self.pos() + diff
        self.move(newpos)
        self.mpos = event.globalPosition().toPoint()
