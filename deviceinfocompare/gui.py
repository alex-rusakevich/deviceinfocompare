import datetime
import logging
import os
import platform
import re
import sys
from typing import Union

from PyQt6 import QtGui, QtWidgets, uic
from PyQt6.QtCore import QStringListModel
from PyQt6.QtWidgets import QMessageBox

import deviceinfocompare
from deviceinfocompare.processors import *
from deviceinfocompare.settings import LOGGING, RESOURCE_PATH

logger = logging.getLogger(__name__)


def strip_s_ms(dt_in: Union[str, datetime.datetime]):
    dt_in = str(dt_in)
    return re.sub(r":\d+\.\d+$", "", dt_in)


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

        system_name = platform.system()
        data_processor = None

        if system_name == "Windows":
            data_processor = WindowsProcessor()
        else:
            raise Exception(f"DIC can't work on {system_name} yet")

        # region Configuring logger
        logTextBox = QTextEditLogger(self.loggingTextEdit)
        logging.getLogger().addHandler(logTextBox)

        logger.info("The program has started")
        # endregion

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
            QtGui.QIcon(os.path.join(RESOURCE_PATH, "ui", "exclamation-red.png"))
        )
        # endregion

        self.connectEvents()

        dump_data_list = reversed(data_processor.get_dump_list())
        entries = (
            f"#0 [{strip_s_ms(datetime.datetime.utcnow())}] Current device list",
            *[f"#{i[0]} [{strip_s_ms(i[1])}] {i[2]}" for i in dump_data_list],
        )

        model = QStringListModel()
        model.setStringList(entries)

        self.leftListView.setModel(model)
        self.rightListView.setModel(model)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()


def run_ui():
    window.show()
    app.exec()
