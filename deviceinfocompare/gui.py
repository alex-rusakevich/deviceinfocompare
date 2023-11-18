import glob
import logging
import os
import sys

from PyQt6 import QtGui, QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox

import deviceinfocompare
from deviceinfocompare.settings import LOGGING, RESOURCE_PATH

logger = logging.getLogger(__name__)


class QTextEditLogger(logging.Handler):
    def __init__(self, textedit_widget):
        super().__init__()
        self.widget = textedit_widget
        self.widget.setReadOnly(True)

        formatter = logging.Formatter(LOGGING["formatters"]["standard"]["format"])
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)


class MainWindow(QtWidgets.QMainWindow):
    def connectEvents(self):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(RESOURCE_PATH, "ui", "deviceinfocompare.ui"), self)

        logTextBox = QTextEditLogger(self.loggingTextEdit)
        logging.getLogger().addHandler(logTextBox)

        logger.info("The program has started")

        self.centralWidget.setContentsMargins(11, 11, 11, 11)
        self.setWindowIcon(
            QtGui.QIcon(os.path.join(RESOURCE_PATH, "ui", "favicon.png"))
        )
        self.setWindowTitle(f"deviceinfocompare v{deviceinfocompare.__version__}")

        # region Initializing error window
        self.err_msg = QMessageBox()
        self.err_msg.setIcon(QMessageBox.Icon.Critical)
        self.err_msg.setWindowTitle("Error")
        self.err_msg.setWindowIcon(
            QtGui.QIcon(os.path.join(RESOURCE_PATH, "ui", "error.png"))
        )
        # endregion

        self.connectEvents()


app = QtWidgets.QApplication(sys.argv)
app.setStyle("Fusion")
window = MainWindow()


def run_ui():
    window.show()
    app.exec()
