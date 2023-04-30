import sys
import os
import time
import threading  
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QTextBrowser, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtWidgets import QPushButton, QLabel, QInputDialog, QDialog, QFormLayout, QStackedLayout, QLineEdit, QMenu
from PyQt6.QtGui import QFont, QPixmap, QAction
from alphageist.query import query_vectorstore
from alphageist.vectorstore import create_vectorstore, vectorstore_exists, load_vectorstore
from langchain.vectorstores.base import VectorStore
from dotenv import load_dotenv

TEST_DATA_PATH = "test/data"
PERSIST_DIRECTORY = ".alphageist"

class SettingsDialog(QDialog):
    # Connected to focus check of Settings window 
    opened = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, api_key, search_folder):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setWindowModality(Qt.WindowModality.NonModal)  # Set the dialog to be non-modal
        self.api_key = api_key
        self.search_folder = search_folder
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Set API key input field 
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setText(self.api_key)
        self.api_key_input.setReadOnly(True)
        self.api_key_input.textChanged.connect(self.enable_save_button)
        self.api_key_input.setMinimumSize(300, 0)
        self.api_key_input.setFixedHeight(30)  # Set the height
        self.api_key_input.setStyleSheet(
            """
                color: gray;
                border-radius: 10px;
            """
            ) 

        # Set edit button for API key field
        self.api_key_edit = QPushButton('✎', self)
        self.api_key_edit.clicked.connect(self.toggle_api_key_edit)
        self.api_key_edit.setStyleSheet(
            """
                color: white; 
                background-color: #629EE4;
                border-radius: 10px;
            """
            )
        self.api_key_edit.setFixedWidth(40)  # Set the width
        self.api_key_edit.setFixedHeight(30)  # Set the height
    
        
        # Set horisontal layout for API key row
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("API Key"))
        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(self.api_key_edit)
        layout.addLayout(api_key_layout)

        # Set search folders input field 
        self.search_folders_input = QLineEdit(self)
        self.search_folders_input.setText(self.search_folder)
        self.search_folders_input.setReadOnly(True)
        self.search_folders_input.textChanged.connect(self.enable_save_button)
        self.search_folders_input.setMinimumSize(300, 0)
        self.search_folders_input.setFixedHeight(30)  # Set the height
        self.search_folders_input.setStyleSheet(
            """
                color: gray; 
                border-radius: 10px;
            """
            ) 

        # Set edit button for search folders field
        self.search_folders_edit = QPushButton('✎', self)
        self.search_folders_edit.clicked.connect(self.toggle_search_folders_edit)
        self.search_folders_edit.setStyleSheet(
            """
                color: white; 
                background-color: #629EE4;
                border-radius: 10px;
            """
            )
        self.search_folders_edit.setFixedWidth(40)  # Set the width
        self.search_folders_edit.setFixedHeight(30)  # Set the height
        
        # Set horisontal layout for Search folders field
        search_folders_layout = QHBoxLayout()
        search_folders_layout.addWidget(QLabel("Search Folders"))
        search_folders_layout.addWidget(self.search_folders_input)
        search_folders_layout.addWidget(self.search_folders_edit)
        layout.addLayout(search_folders_layout)

        # Set Save button 
        self.save_button = QPushButton('Save', self)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_and_close)
        self.save_button.clicked.connect(self.accept)
        self.save_button.setFixedHeight(30)
        self.save_button.setFixedWidth(150)  

        self.save_button.setStyleSheet(
        """
            QPushButton {
                border-radius: 10px; 
                color: #9E9E9E;
            }
            QPushButton:enabled {
                background-color: #629EE4;
                color: white;
            }
            QPushButton:!enabled {
                background-color: #565656;
            }
        """
        )

        layout.addWidget(self.save_button)

        self.setLayout(layout)

    
    def enable_save_button(self):
        # Change state on save button when 
        if (self.api_key_input.text() != self.api_key or self.search_folders_input.text() != self.search_folder):
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)
    
    def save_and_close(self):
        # Here you would typically save the settings
        # ...

        # Emit the 'closed' signal and close the window
        self.closed.emit()
        self.close()

    def toggle_api_key_edit(self):
        self.api_key_input.setReadOnly(not self.api_key_input.isReadOnly())
        self.api_key_input.setStyleSheet("color: white;") # Change color of text in field
        #self.save_button.setEnabled(True)

    def toggle_search_folders_edit(self):
        self.search_folders_input.setReadOnly(not self.search_folders_input.isReadOnly())
        self.search_folders_input.setStyleSheet("color: white;") # Change color of text in field
        #self.save_button.setEnabled(True)

    def showEvent(self, event):
        self.opened.emit()

    def closeEvent(self, event):
        self.closed.emit()


class SpotlightSearch(QWidget):

    vectorstore: VectorStore 
    _loading_vectorstore: bool = False 

    #def __init__(self,docs):
    def __init__(self, path): 
        super().__init__()
        self.mpos = QPoint()
        self.settings_open = False

        # CLI block
        if vectorstore_exists(PERSIST_DIRECTORY):
            self.vectorstore = load_vectorstore(PERSIST_DIRECTORY)
        else:
            self._loading_vectorstore = True
            threading.Thread(target=self._create_vectorstore, args=(path,PERSIST_DIRECTORY)).start()

        # Set up the user interface
        self.init_ui()

        # Set up the timer for checking focus
        self.check_focus_timer = QTimer(self)
        self.check_focus_timer.timeout.connect(self.check_focus)
        self.check_focus_timer.start(500)  # Check every 500 milliseconds

        # Add drop shadow effect
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(20)
        self.shadow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow_effect)
    
    def _create_vectorstore(self, path, persist_vectorstore):
       self.vectorstore = create_vectorstore(path, persist_vectorstore) 
       self._loading_vectorstore = False

    def init_ui(self):

        # CLI
        print("Loading vectorstore", end='')
        cnt = 1
        while self._loading_vectorstore:
            sys.stdout.write(".")
            time.sleep(0.2)
            if cnt%4 == 0:
                sys.stdout.write(4*"\b")
                sys.stdout.write(4*" ")
                sys.stdout.write(4*"\b")
            sys.stdout.flush()
            cnt = cnt + 1
        print("")

        # Set window properties
        self.setMinimumSize(600, 100)
        self.setMaximumSize(600, 100)
        self.center()

        # Remove window frame and background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Create a horizontal layout for search bar and logo
        search_layout = QHBoxLayout()
        search_layout.setSpacing(2)  # Set spacing btween logo and search bar
        
        # Create logo label and load logo image
        self.logo_label = QLabel(self)
        logo_path = os.path.join("frontend_assets", "logo_45x45.png")
        logo_pixmap = QPixmap(logo_path) 
        self.logo_label.setPixmap(logo_pixmap.scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio))  # Adjust logo size
        
        # Create context menu for logo_label
        self.logo_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.logo_label.customContextMenuRequested.connect(self.show_logo_context_menu)

        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.show_settings)
        
        search_layout.addWidget(self.logo_label)

        # Create search bar and set properties
        self.search_bar = QLineEdit(self)
        font = QFont()
        font.setPointSize(20)               # Set size font of search bar text
        self.search_bar.setFont(font)       
        self.search_bar.setFixedHeight(40)  # Adjust the height of search bar
        self.search_bar.setPlaceholderText("Search...") # Set default text in Search bar
        self.search_bar.returnPressed.connect(self.toggle_search_results)
        search_layout.addWidget(self.search_bar)

        
        # Add gear icon for settings (not used atm but saved for potential future use)

        #self.settings_button = QPushButton('⚙', self)
        #self.settings_button.clicked.connect(self.show_settings)
        #self.settings_button.setStyleSheet(
        #    """
        #        color: white;
        #        font: bold 35px;
        #        background-color: #323232;
        #        border-radius: 5px;
        #    """
        #    )
        #self.settings_button.setFixedWidth(40)  # Set the width
        #self.settings_button.setFixedHeight(40)  # Set the height
        #search_layout.addWidget(self.settings_button)


        # Set up the main layout (Search bar + results)
        layout = QVBoxLayout()
        layout.addLayout(search_layout)

        # Create text browser to display search results
        self.search_results = QTextBrowser(self)
        self.search_results.setOpenExternalLinks(True)
        self.search_results.setVisible(False) # Hite search result initially
        self.search_results.setStyleSheet(
            """
            QTextBrowser {
            border: 1px solid #686868;
            border-radius: 10px;
            background-color: #323232;
            }
            """
            )
        layout.addWidget(self.search_results)

        # Set the layout for the widget
        self.setLayout(layout)

        # Set focus on the search bar
        self.search_bar.setFocus()

    def center(self):
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

    def toggle_search_results(self):
        if self.search_bar.text():

            # Get search result string
            response = query_vectorstore(self.vectorstore, self.search_bar.text()) # CLI
            search_result_text = (f"{response['answer']}")
            print(response)
            
            # List of sources
            sources = response['sources'].split(',')

            # Append sources to the search result text
            search_result_text += "<br><br>Sources:" 
            for source in sources:
                search_result_text += f"<br><a href='{source.strip()}'>{source.strip()}</a>"

            self.search_results.setHtml(search_result_text)
            self.search_results.setVisible(True)
            self.adjust_window_size()

        else:
            self.search_results.setVisible(False)  # Hide search results if search bar is empty
            self.adjust_window_size()

    def show_settings(self):
        self.settings_dialog = SettingsDialog("Yktgs45363twrwfdsgjryrehg6433", "test/data")
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

def main():

    path = input("Path (test/data/):")
    path = path if path else TEST_DATA_PATH

    #docs = get_docs_from_path(path)     

    app = QApplication(sys.argv)
    spotlight_search = SpotlightSearch(path)
    spotlight_search.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    load_dotenv()
    main()
