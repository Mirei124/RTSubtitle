import logging
import os
import sys

from PyQt6.QtWidgets import QApplication

from .ui import MainWindow

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING)

os.environ["QT_QPA_PLATFORM"] = "xcb"


def run():
    app = QApplication(sys.argv)
    app.setStyle(MainWindow.get_theme())
    w = MainWindow()
    sys.exit(app.exec())


run()
