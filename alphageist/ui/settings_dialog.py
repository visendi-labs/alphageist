import os

from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QMetaObject, pyqtSlot, QSize
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QTextBrowser, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtWidgets import QPushButton, QLabel, QInputDialog, QDialog, QFormLayout, QStackedLayout, QLineEdit, QMenu, QFileDialog, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont, QPixmap, QAction, QIcon

from .constant import ASSETS_DIRECTORY

class SettingsDialog(QDialog):
    # Connected to focus check of Settings window
    opened = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, api_key, search_folder):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setModal(True)  # Set the dialog to be application modal
        # Add the "stay on top" window flag
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.api_key = api_key
        self.search_folder = search_folder
        self.init_ui()

    def init_ui(self):
        self.init_api_key_settings()    # Set "API key" field
        self.init_search_folder()       # Set "Add search folder" container
        self.init_delete_button()       # Set "Delete" button
        self.init_edit_button()         # Set "Edit" button
        self.init_add_folder_button()   # Set "Add folder" button
        self.init_save_button()         # Set "Save" button
        self.init_saved_folder_path()    # Set previously saved folder (if it exists)
        self.init_layout()              # Set main layout

    def init_api_key_settings(self):
        # Set the API key input row
        # Set API key input field
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setText(self.api_key)
        self.api_key_input.setReadOnly(True)
        self.api_key_input.textChanged.connect(self.update_save_button_state)
        self.api_key_input.setMinimumSize(450, 0)
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
        self.api_key_edit.setFixedWidth(40)
        self.api_key_edit.setFixedHeight(30)
        # Set horisontal layout for API key row
        self.api_key_layout = QHBoxLayout()
        self.api_key_layout.addWidget(QLabel("API Key"))
        self.api_key_layout.addWidget(self.api_key_input)
        self.api_key_layout.addWidget(self.api_key_edit)

    def init_search_folder(self):
        # Set the Search folder container which holds a folder icon and path to chosen search folder
        # Set folder display container
        self.folder_container = QWidget(self)
        self.folder_container.setStyleSheet(
            """
            background-color: #252525; 
            border-radius: 10px;
            """
        )
        self.folder_container.setFixedWidth(500)
        self.folder_container.setFixedHeight(40)
        # Add drop shadow effect to folder container
        shadow_effect = QGraphicsDropShadowEffect(self.folder_container)
        shadow_effect.setBlurRadius(15)
        shadow_effect.setOffset(2)
        shadow_effect.setColor(Qt.GlobalColor.black)  # Set shadow color
        self.folder_container.setGraphicsEffect(shadow_effect)
        # Initially hide the folder display container
        self.folder_container.hide()
        # Set layout for folder display container
        folder_layout = QHBoxLayout(self.folder_container)
        # Margins left, top, right, bottom
        folder_layout.setContentsMargins(10, 0, 0, 0)
        folder_layout.setSpacing(10)  # Spacing between elements in layout
        # Set folder icon
        folder_icon = QLabel(self.folder_container)
        folder_icon_path = os.path.join(
            ASSETS_DIRECTORY, "folder_icon_1200x1200.png")
        folder_icon.setPixmap(QPixmap(folder_icon_path).scaled(
            25, 25, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        folder_icon.setFixedSize(25, 25)
        folder_layout.addWidget(folder_icon)
        # Set folder path text field
        self.folder_path = QLineEdit(self.folder_container)
        self.folder_path.setStyleSheet("color: white;")
        self.folder_path.setReadOnly(True)
        self.folder_path.textChanged.connect(self.update_save_button_state)
        folder_layout.addWidget(self.folder_path)

    def init_delete_button(self):
        # Set the search folder delete button
        self.delete_folder_button = QPushButton(self)
        delete_folder_icon_path = os.path.join(
            ASSETS_DIRECTORY, "trash_can_1200x1200.png")
        self.delete_folder_button.setIcon(
            QIcon(QPixmap(delete_folder_icon_path)))
        self.delete_folder_button.setIconSize(QSize(25, 25))
        self.delete_folder_button.setStyleSheet(
            """
            background-color: #E06060; 
            border-radius: 10px;
            """
        )
        self.delete_folder_button.setFixedWidth(35)
        self.delete_folder_button.setFixedHeight(35)
        self.delete_folder_button.clicked.connect(self.remove_folder)
        self.delete_folder_button.hide()  # Initially hide the button

    def init_edit_button(self):
        # Set the edit search folder button
        self.edit_folder_button = QPushButton('✎', self)
        self.edit_folder_button.setStyleSheet(
            """
                color: white; 
                background-color: #629EE4;
                border-radius: 10px;
            """
        )
        self.edit_folder_button.setFixedWidth(35)
        self.edit_folder_button.setFixedHeight(35)
        self.edit_folder_button.clicked.connect(self.add_folder)
        self.edit_folder_button.hide()  # Initially hide the button

    def init_add_folder_button(self):
        # Set the add folder button
        self.add_folder_button = QPushButton('+ Add', self)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.add_folder_button.setStyleSheet(
            """
            background-color: #629EE4; 
            border-radius: 10px;
            """
        )
        self.add_folder_button.setFixedWidth(70)
        self.add_folder_button.setFixedHeight(30)

    def init_save_button(self):
        # Set save button design and intial state
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

    def init_layout(self):
        # Set the vertical layout inside the settings window
        self.layout = QVBoxLayout()
        # Add API key layout to main layout
        self.layout.addLayout(self.api_key_layout)
        # Create empty space after the API key row
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum,
                             QSizePolicy.Policy.MinimumExpanding)
        self.layout.addItem(spacer)
        # Add "Choose Folders" label
        self.layout.addWidget(QLabel("Choose Folders"))
        # Set horisontal layout for "Search Folder container" with edit & delete button
        self.folder_display_layout = QHBoxLayout()
        self.folder_display_layout.addWidget(
            self.folder_container)  # Add search folder container
        self.folder_display_layout.addWidget(
            self.edit_folder_button)  # Add edit button
        self.folder_display_layout.addWidget(
            self.delete_folder_button)  # Add delete button
        # Add "Search folder container" to main layout
        self.layout.addLayout(self.folder_display_layout)
        # Add "Add button" to main layout
        self.layout.addWidget(self.add_folder_button)
        # Add empty space after the "Add folder" row
        self.layout.addItem(spacer)
        # Add "Save button" to main layout
        self.layout.addWidget(self.save_button)
        # Set main layout
        self.setLayout(self.layout)

    def update_save_button_state(self):
        # Update state on the "Save button" if user has made any changes in the Settings window
        if (self.api_key_input.text() != self.api_key or self.folder_path.text() != self.search_folder):
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)

    def save_and_close(self):
        # Add changes made in the settings window
        # Emit the 'closed' signal and close the window
        self.closed.emit()
        self.close()

    def toggle_api_key_edit(self):
        # When user want to edit the API key field
        self.api_key_input.setReadOnly(not self.api_key_input.isReadOnly())
        # Change color of text in field
        self.api_key_input.setStyleSheet("color: white;")

    def init_saved_folder_path(self):
        # Check if any search folders has been previously saved
        if self.search_folder:
            self.folder_path.setText(self.search_folder)
            self.folder_container.show()
            self.delete_folder_button.show()
            self.edit_folder_button.show()
            self.add_folder_button.hide()
        else:
            self.folder_container.hide()

    def add_folder(self):
        # Lets user choose a search folder via a file dialog window, after pressing on the "+Add" button
        self.added_folder_path = str(
            QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.added_folder_path:
            self.folder_path.setText(self.added_folder_path)
            self.folder_container.show()
            self.delete_folder_button.show()
            self.edit_folder_button.show()
            self.add_folder_button.hide()
            self.update_save_button_state()
        else:
            self.folder_container.hide()

    def remove_folder(self):
        # Removes chosen search folder, after user has pressed on the trash can button (aka "delete button")
        self.folder_path.clear()
        self.folder_container.hide()
        self.delete_folder_button.hide()
        self.edit_folder_button.hide()
        self.add_folder_button.show()
        self.update_save_button_state()

    def showEvent(self, event):
        self.opened.emit()

    def closeEvent(self, event):
        self.closed.emit()
