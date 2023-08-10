import sys
import time
import os
from PyQt6.QtWidgets import (
    QApplication, 
    QProgressDialog, 
    QPushButton, 
    QVBoxLayout, 
    QWidget, 
    QLabel,
    QProgressBar
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

from PyQt6.QtGui import (
    QFont, 
    QPixmap, 
    QAction, 
    QIcon, 
    QCursor
)
from alphageist.ui.constant import (
    COLOR,
    DESIGN,
    ASSETS_DIRECTORY
)
from alphageist.ui import util

class Logo(QLabel):
    def __init__(self):
        super().__init__()
        logo_path = util.resource_path(os.path.join(ASSETS_DIRECTORY, "logo_V_only_311x316.png"))
        logo_pixmap = QPixmap(logo_path)
        self.setPixmap(logo_pixmap.scaled(
            311, 316, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self.setStyleSheet(f"""
        border: 0px solid white;
                """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

class ProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setGeometry(50, 100, 250, 30)
        self.setValue(66)

class UpdateWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFixedWidth(400)
        self.setStyleSheet(f"""
        color: {COLOR.MOONLIT_SNOW};
        font-size: 22px;
        font-weight: bold;
        font-family: {DESIGN.FONT_FAMILY};
        background-color: {COLOR.OBSIDIAN_SHADOW}; 
        """)
        layout = QVBoxLayout(self)
        self.logo = Logo()
        self.label = QLabel('Updating...')
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prg_bar = ProgressBar()
        layout.addWidget(self.logo)
        layout.addWidget(self.label)
        layout.addWidget(self.prg_bar)
        self.setLayout(layout)

    def progress_hook(self, bytes_downloaded: int, bytes_expected: int):
        progress_percent = bytes_downloaded / bytes_expected * 100
        self.prg_bar.setValue(int(progress_percent))


