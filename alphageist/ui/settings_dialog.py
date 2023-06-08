
import os

from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QMetaObject, pyqtSlot, QSize
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QTextBrowser, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtWidgets import QPushButton, QLabel, QInputDialog, QDialog, QFormLayout, QStackedLayout, QLineEdit, QMenu, QFileDialog, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QFont, QPixmap, QAction, QIcon, QMouseEvent

from .constant import ASSETS_DIRECTORY
from .constant import COLOR
from .constant import DESIGN
from alphageist import config as cfg
from alphageist.ui import util


class SettingsDialog(QDialog):
    # Connected to focus check of Settings window
    opened = pyqtSignal()
    closed = pyqtSignal(bool)

    def __init__(self, config: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config  # Only updated when saved
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setModal(True)  # Set the dialog to be application modal
        # Add the "stay on top" window flag
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.FramelessWindowHint)
        # Set global style sheet for settings dialog
        self.setStyleSheet(f"""
            color: {COLOR.WHITE};
            font-family: {DESIGN.FONT_FAMILY};
            QPushButton {{
                font-size: 25px;
            }}
        """)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.init_title_bar()           # Set the title bar
        self.init_api_key_settings()    # Set "API key" field
        self.init_search_folder()       # Set "Add search folder" container
        self.init_delete_button()       # Set "Delete" button
        self.init_edit_button()         # Set "Edit" button
        self.init_add_folder_button()   # Set "Add folder" button
        self.init_save_button()         # Set "Save" button
        self.init_cancel_button()       # Set "Cancel" button
        self.init_layout()              # Set main layout
        self.init_background()          # Set the background
        self.init_outer_layout()        # Set outer layout

        # Set main layout
        self.setLayout(self.outer_layout)

    def init_title_bar(self):
        self.title_bar = QWidget()
        self.title_bar.setStyleSheet(
            f"""
            background-color: {COLOR.OBSIDIAN_SHADOW};
            border-top-right-radius: {DESIGN.ELEMENT_RADIUS};
            border-top-left-radius: {DESIGN.ELEMENT_RADIUS};
            """)

        self.title_label = QLabel('Settings')
        self.title_label.setStyleSheet(
            f"""
            color: {COLOR.WHITE};
            font-weight: bold;
            """)

        self.title_bar_layout = QHBoxLayout()

        spacer_left = QSpacerItem(
            20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(
            20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.title_bar_layout.addItem(spacer_left)   # Add spacer to the left
        self.title_bar_layout.addWidget(self.title_label)  # Add your label
        self.title_bar_layout.addItem(spacer_right)  # Add spacer to the right

        self.title_bar.setLayout(self.title_bar_layout)

    def init_api_key_settings(self):
        # Set the API key input row
        # Set API key input field
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setText(self.config.get(cfg.API_KEY_OPEN_AI, ""))
        self.api_key_input.textChanged.connect(self.update_save_button_state)
        self.api_key_input.setMinimumSize(450, 0)
        self.api_key_input.setFixedHeight(30)  # Set the height
        self.api_key_input.setStyleSheet(f"""
                color: {COLOR.WHITE};
                background-color: {COLOR.OBSIDIAN_SHADOW};
                border-radius: {DESIGN.ELEMENT_RADIUS};
            """)

        # Set horisontal layout for API key row
        self.api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key")
        api_key_label.setStyleSheet(f"color: {COLOR.WHITE};")
        self.api_key_layout.addWidget(api_key_label)
        self.api_key_layout.addWidget(self.api_key_input)

    def init_search_folder(self):
        # Set the Search folder container which holds a folder icon and path to chosen search folder
        # Set folder display container
        self.folder_container = QWidget(self)
        self.folder_container.setStyleSheet(
            f"""
            background-color: {COLOR.OBSIDIAN_SHADOW}; 
            border-radius: {DESIGN.BUTTON_RADIUS};
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
        folder_icon_path = util.resource_path(os.path.join(
            ASSETS_DIRECTORY, "folder_icon_1200x1200.png"))
        folder_icon.setPixmap(QPixmap(folder_icon_path).scaled(
            25, 25, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        folder_icon.setFixedSize(25, 25)
        folder_layout.addWidget(folder_icon)
        # Set folder path text field
        self.folder_path = QLineEdit(self.folder_container)
        self.folder_path.setStyleSheet(f"color: {COLOR.WHITE};")
        self.folder_path.setReadOnly(True)
        self.folder_path.textChanged.connect(self.update_save_button_state)
        folder_layout.addWidget(self.folder_path)

    def init_delete_button(self):
        # Set the search folder delete button
        self.delete_folder_button = QPushButton(self)
        delete_folder_icon_path = util.resource_path(os.path.join(
            ASSETS_DIRECTORY, "trash_can_1200x1200.png"))
        self.delete_folder_button.setIcon(
            QIcon(QPixmap(delete_folder_icon_path)))
        self.delete_folder_button.setIconSize(QSize(25, 25))
        self.delete_folder_button.setStyleSheet(
            f"""
            QPushButton{{
                    background-color: {COLOR.SUNSET_RED};
                    border-radius: {DESIGN.BUTTON_RADIUS};
                }}
            QPushButton:hover{{
                    background-color: {COLOR.APRICOT_BREEZE};
                }}
            """
        )
        self.delete_folder_button.setFixedWidth(DESIGN.BUTTON_ICON_WIDTH)
        self.delete_folder_button.setFixedHeight(DESIGN.BUTTON_ICON_WIDTH)
        self.delete_folder_button.clicked.connect(self.remove_folder)
        self.delete_folder_button.hide()  # Initially hide the button

    def init_edit_button(self):
        # Set the edit search folder button
        self.edit_folder_button = QPushButton(self)
        icon_path = util.resource_path(os.path.join(ASSETS_DIRECTORY, "pen_icon_1200x1200.png"))
        self.edit_folder_button.setIcon(
            QIcon(QPixmap(icon_path))
        )
        self.edit_folder_button.setStyleSheet(
            f"""
            QPushButton{{
                    background-color: {COLOR.COSMIC_SAPPHIRE};
                    border-radius: {DESIGN.BUTTON_RADIUS};
                }}
            QPushButton:hover{{
                    background-color: {COLOR.DREAMY_SKY};
                }}
            """
        )
        self.edit_folder_button.setFixedWidth(DESIGN.BUTTON_ICON_WIDTH)
        self.edit_folder_button.setFixedHeight(DESIGN.BUTTON_ICON_HEIGHT)
        self.edit_folder_button.clicked.connect(self.add_folder)
        self.edit_folder_button.hide()  # Initially hide the button

    def init_add_folder_button(self):
        # Set the add folder button
        self.add_folder_button = QPushButton('+ Add', self)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.add_folder_button.setStyleSheet(
            f"""
            QPushButton{{
                    color: {COLOR.WHITE};
                    background-color: {COLOR.COSMIC_SAPPHIRE};
                    border-radius: {DESIGN.BUTTON_RADIUS};
                }}
            QPushButton:hover{{
                    background-color: {COLOR.DREAMY_SKY};
                }}
            """
        )
        self.add_folder_button.setFixedWidth(DESIGN.BUTTON_ADD_FOLDER_WIDTH)
        self.add_folder_button.setFixedHeight(DESIGN.BUTTON_HEIGHT)

    def init_save_button(self):
        # Set save button design and intial state
        self.save_button = QPushButton('Save', self)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_and_close)
        self.save_button.clicked.connect(self.accept)
        self.save_button.setFixedHeight(DESIGN.BUTTON_HEIGHT)
        self.save_button.setFixedWidth(DESIGN.BUTTON_SAVE_WIDTH)
        self.save_button.setStyleSheet(
            f"""
            QPushButton {{
                border-radius: {DESIGN.BUTTON_RADIUS}; 
                font-size: {DESIGN.BUTTON_FONT_SIZE};
            }}
            QPushButton:enabled {{
                background-color: {COLOR.COSMIC_SAPPHIRE};
                color: {COLOR.WHITE};
            }}
            QPushButton:enabled:hover {{
                background-color: {COLOR.DREAMY_SKY};
            }}
            QPushButton:!enabled {{
                background-color: {COLOR.DOVE_GRAY};
                color: {COLOR.GRAPHITE_DUST};
            }}
        """
        )

    def init_cancel_button(self):
        # Set cancel button design and intial state
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.clicked.connect(self.accept)
        self.cancel_button.setFixedHeight(DESIGN.BUTTON_HEIGHT)
        self.cancel_button.setFixedWidth(DESIGN.BUTTON_CANCEL_WIDTH)
        self.cancel_button.setStyleSheet(
            f"""
            QPushButton {{
                font-size: {DESIGN.BUTTON_FONT_SIZE};
                border: 1px solid {COLOR.STEEL_HAZE};
                border-radius: {DESIGN.BUTTON_RADIUS}; 
                color: {COLOR.WHITE};
            }}
            QPushButton:hover {{
                background-color: {COLOR.DOVE_GRAY};  
            }}"""
        )

    def init_layout(self):

        self.layout = QVBoxLayout()
        margin = 15
        self.layout.setContentsMargins(margin, margin, margin, margin)
        # Add API key layout to main layout
        self.layout.addLayout(self.api_key_layout)

        # Create empty space after the API key row
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum,
                             QSizePolicy.Policy.MinimumExpanding)
        self.layout.addItem(spacer)
        # Add "Choose Folders" label
        choose_folders_label = QLabel("Choose Folders")
        choose_folders_label.setStyleSheet(f"color: {COLOR.WHITE};")
        self.layout.addWidget(choose_folders_label)
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

        # Create a layout for the save & cancel buttons
        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

    def init_background(self):
        self.background_widget = QWidget()
        self.background_widget.setStyleSheet(
            f"""
            background-color: {COLOR.GRAPHITE_DUST};
            border-bottom-right-radius: {DESIGN.ELEMENT_RADIUS};
            border-bottom-left-radius: {DESIGN.ELEMENT_RADIUS};
            """
        )
        self.background_widget.setLayout(self.layout)

    def init_outer_layout(self):
        # Set the vertical layout inside the settings window
        # Outer layout contains the titlebar + the layout
        self.outer_layout = QVBoxLayout()
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(0)
        self.outer_layout.addWidget(self.title_bar)
        self.outer_layout.addWidget(self.background_widget)

    @property
    def settings_has_changed(self)->bool:
        return (self.api_key_input.text() != self.config[cfg.API_KEY_OPEN_AI] or 
            self.folder_path.text() != self.config[cfg.SEARCH_DIRS])

    def update_save_button_state(self):

        # Update state on the "Save button" if user has made any changes in the Settings window
        if self.settings_has_changed:
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)

    def close(self, config_changed:bool=False):
        self.closed.emit(config_changed)
        super().close()

    def reset_to_config(self):
        self.api_key_input.setText(self.config[cfg.API_KEY_OPEN_AI])
        self.init_saved_folder_path()

    def save_and_close(self):
        
        # Update the config object
        self.config[cfg.API_KEY_OPEN_AI] = self.api_key_input.text()
        self.config[cfg.SEARCH_DIRS] = self.folder_path.text()

        # Save the config to file
        cfg_file_path = cfg.get_config_file_path()
        cfg.save_config(cfg_file_path, self.config)


        # Emit the 'closed' signal and close the window
        self.close(config_changed=True)

    def init_saved_folder_path(self):
        # Check if any search folders has been previously saved
        if self.config.get(cfg.SEARCH_DIRS, ""):
            self.folder_path.setText(self.config[cfg.SEARCH_DIRS])
            self.folder_container.show()
            self.delete_folder_button.show()
            self.edit_folder_button.show()
            self.add_folder_button.hide()
        else:
            self.folder_container.hide()

    def add_folder(self):
        # Lets user choose a search folder via a file dialog window, after pressing on the "+Add" button
        folder_path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if folder_path:
            self.added_folder_path = folder_path
            self.folder_path.setText(self.added_folder_path)
            self.folder_container.show()
            self.delete_folder_button.show()
            self.edit_folder_button.show()
            self.add_folder_button.hide()
            self.update_save_button_state()

    def remove_folder(self):
        # Removes chosen search folder, after user has pressed on the trash can button (aka "delete button")
        self.folder_path.clear()
        self.folder_container.hide()
        self.delete_folder_button.hide()
        self.edit_folder_button.hide()
        self.add_folder_button.show()
        self.update_save_button_state()

    def show(self):
        self.reset_to_config()
        super().show()

    def showEvent(self, event):
        self.opened.emit()

    def closeEvent(self, event):
        self.closed.emit(False)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
