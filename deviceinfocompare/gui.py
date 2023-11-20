import datetime
import logging
import os
import platform
import re
import sys
from ast import dump
from typing import Union

from PyQt6 import QtGui, QtWidgets, uic
from PyQt6.QtCore import QObject, QStringListModel, QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from showinfm import show_in_file_manager

import deviceinfocompare
from deviceinfocompare.processors import *
from deviceinfocompare.settings import BASE_DIR, LOGGING, RESOURCE_PATH

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
    # region Events
    def on_event_revealDBPushButton_clicked(self):
        db_dir = os.path.join(BASE_DIR, "deviceinfo.db")
        logger.debug(db_dir)

        show_in_file_manager(
            db_dir,
            open_not_select_directory=True,
            allow_conversion=True,
        )

    def on_event_addPushButton_clicked(self):
        class Worker(QObject):
            finished = pyqtSignal()

            def __init__(self, *args, **kwargs):
                self.data_processor = kwargs.pop("data_processor")
                self.title = kwargs.pop("title")
                super().__init__(*args, **kwargs)

            def run(self):
                self.data_processor.dump_devices(self.title)
                self.finished.emit()

        title = self.dumpTitleLineEdit.text().strip() or "Unnamed dump"

        self.add_dump_thread = QThread()
        self.add_dump_worker = Worker(data_processor=self.data_processor, title=title)
        self.add_dump_worker.moveToThread(self.add_dump_thread)

        self.add_dump_thread.started.connect(self.add_dump_worker.run)
        self.add_dump_worker.finished.connect(self.add_dump_thread.quit)
        self.add_dump_worker.finished.connect(self.add_dump_worker.deleteLater)
        self.add_dump_thread.finished.connect(self.add_dump_thread.deleteLater)

        logger.info(f"Started making dump '{title}'")
        self.setAllButtonsEnabled(False)
        self.add_dump_thread.start()

        self.add_dump_thread.finished.connect(lambda: self.populateDumpLists())
        self.add_dump_thread.finished.connect(lambda: self.setAllButtonsEnabled(True))
        self.add_dump_thread.finished.connect(
            lambda: logger.info("The new dump has been created!")
        )

    def on_event_deletePushButton_clicked(self):
        class Worker(QObject):
            finished = pyqtSignal()

            def __init__(self, *args, **kwargs):
                self.data_processor = kwargs.pop("data_processor")
                self.dump_id = kwargs.pop("dump_id")
                super().__init__(*args, **kwargs)

            def run(self):
                self.data_processor.remove_dump(self.dump_id)
                self.finished.emit()

        item_val = self.leftListView.currentIndex().data()
        logger.debug(f"item data is '{item_val}'")
        dump_id = -1

        if item_val == None:
            logger.warning("No item was selected on the left panel, stopping")
            return

        dump_id = int(re.search(r"(?<=#)\d+(?=\s)", item_val).group())

        if dump_id == 0:
            logger.warning("Cannot delete dump #0: it's abstract")
            return

        self.delete_dump_thread = QThread()
        self.delete_dump_worker = Worker(
            data_processor=self.data_processor, dump_id=dump_id
        )
        self.delete_dump_worker.moveToThread(self.delete_dump_thread)

        self.delete_dump_thread.started.connect(self.delete_dump_worker.run)
        self.delete_dump_worker.finished.connect(self.delete_dump_thread.quit)
        self.delete_dump_worker.finished.connect(self.delete_dump_worker.deleteLater)
        self.delete_dump_thread.finished.connect(self.delete_dump_thread.deleteLater)

        logger.info(f"Started deleting dump with id {dump_id}")
        self.setAllButtonsEnabled(False)
        self.delete_dump_thread.start()

        self.delete_dump_thread.finished.connect(lambda: self.populateDumpLists())
        self.delete_dump_thread.finished.connect(
            lambda: self.setAllButtonsEnabled(True)
        )
        self.delete_dump_thread.finished.connect(
            lambda: logger.info("The dump has been deleted successfully!")
        )

    # endregion

    def connectEvents(self):
        self.revealDBPushButton.clicked.connect(
            self.on_event_revealDBPushButton_clicked
        )
        self.addPushButton.clicked.connect(self.on_event_addPushButton_clicked)
        self.deletePushButton.clicked.connect(self.on_event_deletePushButton_clicked)

    def populateDumpLists(self):
        self.leftListView.setModel(QStringListModel())
        self.rightListView.setModel(QStringListModel())

        dump_data_list = reversed(self.data_processor.get_dump_list())
        entries = (
            f"#0 [{strip_s_ms(datetime.datetime.utcnow())}] Current device list",
            *[f"#{i[0]} [{strip_s_ms(i[1])}] {i[2]}" for i in dump_data_list],
        )

        model = QStringListModel()
        model.setStringList(entries)

        self.entries = entries
        self.leftListView.setModel(model)
        self.rightListView.setModel(model)

    def setAllButtonsEnabled(self, desired_state: bool = True) -> None:
        for button in (
            self.comparePushButton,
            self.deletePushButton,
            self.addPushButton,
        ):
            button.setEnabled(desired_state)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(RESOURCE_PATH, "ui", "deviceinfocompare.ui"), self)

        system_name = platform.system()
        self.data_processor = None

        if system_name == "Windows":
            self.data_processor = WindowsProcessor()
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

        self.populateDumpLists()
        self.connectEvents()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()


def run_ui():
    window.show()
    app.exec()
