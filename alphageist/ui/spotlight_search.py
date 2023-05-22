import os
import re
import threading

from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QMetaObject, pyqtSlot, QSize
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QTextBrowser, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtWidgets import QPushButton, QLabel, QInputDialog, QDialog, QFormLayout, QStackedLayout, QLineEdit, QMenu, QFileDialog, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont, QPixmap, QAction, QIcon

from alphageist.query import query_vectorstore
from alphageist.vectorstore import create_vectorstore, vectorstore_exists, load_vectorstore
from alphageist.callbackhandler import CustomStreamHandler
from langchain.vectorstores.base import VectorStore
from langchain.schema import LLMResult

from .constant import ASSETS_DIRECTORY
from .constant import PERSIST_DIRECTORY
from .settings_dialog import SettingsDialog

_icon_by_filetype = {
    ".txt": "txt.png",
    ".pdf": "pdf.png",
    ".csv": "csv.png",
    ".py": "python.png",
    ".go": "golang.png",
    ".pptx": "pptx.png",
    ".docx": "word.png",
    "default": "default_file.png"
}


def _get_image_path_by_filename(filename: str) -> str:
    _, file_extension = os.path.splitext(filename)
    return _icon_by_filetype.get(file_extension, _icon_by_filetype["default"])


class SpotlightSearch(QWidget):

    vectorstore: VectorStore
    _loading_vectorstore: bool = False
    update_search_results_signal = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.mpos = QPoint()
        self.settings_open = False
        self.search_folder_path = path
        # Load vectorstore on a separate thread
        if vectorstore_exists(PERSIST_DIRECTORY):
            self.vectorstore = load_vectorstore(PERSIST_DIRECTORY)
        else:
            self._loading_vectorstore = True
            vectorstore_loading_thread = threading.Thread(
                target=self._create_vectorstore, args=(path, PERSIST_DIRECTORY))
            vectorstore_loading_thread.daemon = True
            vectorstore_loading_thread.start()
        # Set up the user interface
        self.init_ui()
        # Set up the timer for checking focus
        self.check_focus_timer = QTimer(self)
        self.check_focus_timer.timeout.connect(self.check_focus)
        self.check_focus_timer.start(500)
        # Set up the timer for checking if vectorstore i loaded
        self.vectorstore_status_timer = QTimer(self)
        self.vectorstore_status_timer.timeout.connect(
            self._check_vectorstore_status)
        self.vectorstore_status_timer.start(100)
        self.setFocus()  # Sets focus so the program wont shutdown
        # Set up the callback functionality making streaming possible
        self.init_callback()

    def init_callback(self):
        self.raw_response = []
        self.callback = CustomStreamHandler(
            self.on_llm_new_token, self.on_llm_end)
        self.muted = False
        self.update_search_results_signal.connect(self.update_search_results)

    @pyqtSlot(str)
    def update_search_results(self, text: str):
        self.search_results.setHtml(text)
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
        self.search_results.setVisible(True)
        self.adjust_window_size()

    def _get_sources_from_answer(self, answer: str) -> list[str]:
        if re.search(r"SOURCES:\s", answer):
            _, sources = re.split(r"SOURCES:\s", answer)
        else:
            sources = ""
        return sources.split(',')

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        answer = response.generations[0][0].text
        sources = self._get_sources_from_answer(answer)
        # Append sources to the search result text
        search_result_text = self.search_results.toHtml()
        search_result_text += "Sources:"
        search_result_text += "<table>"
        for source in sources:
            icon_path = os.path.join(ASSETS_DIRECTORY, _get_image_path_by_filename(source))
            search_result_text += f"""<tr>
<td style='padding-right: 4px;'>
<img src='{icon_path}' width='16' height='16' style='vertical-align: middle;' />
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

    def _check_vectorstore_status(self):
        if self._loading_vectorstore:
            self.search_bar.setPlaceholderText("Loading vectorstore...")
            self.search_bar.setEnabled(False)
        else:
            self.search_bar.setPlaceholderText("Search...")
            self.search_bar.setEnabled(True)

    def _create_vectorstore(self, path, persist_vectorstore):
        self.vectorstore = create_vectorstore(path, persist_vectorstore)
        self._loading_vectorstore = False

    def init_ui(self):
        # Set window properties
        self.set_window_properties()
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
        logo_path = os.path.join(ASSETS_DIRECTORY, "logo2_45x45.png")
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
        font.setPointSize(20)  # Set size font of search bar text
        self.search_bar.setFont(font)
        self.search_bar.setFixedHeight(42)  # Adjust the height of search bar
        # Set default text in Search bar
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.returnPressed.connect(self.search)

    def create_search_results(self):
        self.search_results = QTextBrowser(self)
        self.search_results.setOpenExternalLinks(True)
        self.search_results.setVisible(False)  # Hide search result initially
        self.search_results.setStyleSheet(
            """
            QTextBrowser {
            border: 1px solid #686868;
            border-radius: 10px;
            background-color: #323232;
            }
            """
        )

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
        if not self.settings_open and not self.hasFocus() and not self.search_bar.hasFocus() and not self.search_results.hasFocus():
            self.close()

    def search(self):
        if not self.search_bar.text():
            self.search_results.setVisible(False)
            self.adjust_window_size()
            return
        query_thread = threading.Thread(target=query_vectorstore,
                                        args=(self.vectorstore,
                                              self.search_bar.text()),
                                        kwargs={"callbacks": [self.callback]})
        query_thread.daemon = True
        query_thread.start()

    def show_settings(self):
        # If the settings dialog already exists, show it and don't create a new
        if hasattr(self, 'settings_dialog'):
            self.settings_dialog.show()
        else:
            self.settings_dialog = SettingsDialog(
                "Yktgs45363twrwfdsgjryrehg6433", self.search_folder_path)
            self.settings_dialog.opened.connect(self.settings_opened)
            self.settings_dialog.closed.connect(self.settings_closed)
            self.settings_dialog.show()

    def show_logo_context_menu(self, position):
        context_menu = QMenu(self)
        context_menu.addAction(self.settings_action)
        context_menu.exec(self.logo_label.mapToGlobal(position))

    def settings_opened(self):
        self.settings_open = True

    def settings_closed(self):
        self.settings_open = False

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
