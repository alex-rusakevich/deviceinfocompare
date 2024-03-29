import datetime
import logging
import os
import platform
import re
import sys
import webbrowser
from typing import Optional, Union

from PyQt6 import QtGui, QtWidgets, uic
from PyQt6.QtCore import QObject, QStringListModel, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QListView, QMessageBox, QTextEdit
from showinfm import show_in_file_manager

import deviceinfocompare
from deviceinfocompare.compare import compare_device_list
from deviceinfocompare.processors import *
from deviceinfocompare.settings import BASE_DIR, LOGGING, RESOURCE_PATH

logger = logging.getLogger(__name__)


def strip_s_ms(dt_in: Union[str, datetime.datetime]):
    dt_in = str(dt_in)
    return re.sub(r":\d+\.\d+$", "", dt_in)


class QTextEditLogger(logging.Handler):
    def __init__(self, textedit_widget: QTextEdit):
        super().__init__()
        self.widget = textedit_widget
        self.widget.setReadOnly(True)

        formatter = logging.Formatter(LOGGING["formatters"]["standard"]["format"])
        self.setFormatter(formatter)

    def emit(self, record):
        COLOR_SIGNS = (
            ("[WARNING]", "darkorange"),
            ("[ERROR]", "red"),
            ("[-]", "red"),
            ("[+]", "green"),
            ("[?]", "darkorange"),
            ("[DEBUG]", "magenta"),
        )

        text_color = ""
        msg = self.format(record)

        for sign, color in COLOR_SIGNS:
            if sign in msg:
                text_color = color

        text_color_attrib = "" if text_color == "" else f'style="color: {text_color};"'

        self.widget.append(f"<span {text_color_attrib}>{msg}</span>")
        self.widget.verticalScrollBar().setValue(
            self.widget.verticalScrollBar().maximum()
        )


class TryWorker(QObject):
    def run(self):
        try:
            return self.worker_fn()
        except:
            logger.exception("")
            sys.exit(-1)


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
        class Worker(TryWorker):
            finished = pyqtSignal()

            def __init__(self, *args, **kwargs):
                self.data_processor = kwargs.pop("data_processor")
                self.title = kwargs.pop("title")
                super().__init__(*args, **kwargs)

            def worker_fn(self):
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

        logger.info(f"Started making dump '{title}', please, wait...")
        self.setAllControlsEnabled(False)
        self.add_dump_thread.start()

        self.add_dump_thread.finished.connect(lambda: self.populateDumpLists())
        self.add_dump_thread.finished.connect(lambda: self.setAllControlsEnabled(True))
        self.add_dump_thread.finished.connect(
            lambda: logger.info("The new dump has been created!")
        )

    def on_event_deletePushButton_clicked(self):
        class Worker(TryWorker):
            finished = pyqtSignal()

            def __init__(self, *args, **kwargs):
                self.data_processor = kwargs.pop("data_processor")
                self.dump_id = kwargs.pop("dump_id")
                super().__init__(*args, **kwargs)

            def worker_fn(self):
                self.data_processor.remove_dump(self.dump_id)
                self.finished.emit()

        dump_id = self.getDumpIDfromListView(self.leftListView)

        if dump_id == None:
            logger.error("No item was selected on the left panel, stopping")
            return
        elif dump_id == 0:
            logger.error(
                "Cannot delete dump #0: it's an abstract dump for current device set"
            )
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
        self.setAllControlsEnabled(False)
        self.delete_dump_thread.start()

        self.delete_dump_thread.finished.connect(lambda: self.populateDumpLists())
        self.delete_dump_thread.finished.connect(
            lambda: self.setAllControlsEnabled(True)
        )
        self.delete_dump_thread.finished.connect(
            lambda: logger.info("The dump has been deleted successfully!")
        )

    def on_event_comparePushButton_clicked(self):
        class Worker(TryWorker):
            finished = pyqtSignal()

            def __init__(self, *args, **kwargs):
                self.data_processor = kwargs.pop("data_processor")
                self.left_dump_id = kwargs.pop("left_dump_id")
                self.right_dump_id = kwargs.pop("right_dump_id")
                super().__init__(*args, **kwargs)

            def worker_fn(self):
                device_seq_left = None
                if self.left_dump_id == 0:
                    device_seq_left = self.data_processor.get_current_devices()
                else:
                    device_seq_left = self.data_processor.get_devices_by_dump_id(
                        self.left_dump_id
                    )

                device_seq_right = None
                if self.right_dump_id == 0:
                    device_seq_right = self.data_processor.get_current_devices()
                else:
                    device_seq_right = self.data_processor.get_devices_by_dump_id(
                        self.right_dump_id
                    )

                compare_device_list(device_seq_right, device_seq_left)

                self.finished.emit()

        left_id = self.getDumpIDfromListView(self.leftListView)
        right_id = self.getDumpIDfromListView(self.rightListView)

        if left_id == None:
            logger.error("No item was selected on the left panel, stopping")
            return
        if right_id == None:
            logger.error("No item was selected on the right panel, stopping")
            return
        if left_id == right_id:
            logger.error("Cannot compare the same dumps, stopping")
            return

        self.compare_dump_thread = QThread()
        self.compare_dump_worker = Worker(
            data_processor=self.data_processor,
            left_dump_id=left_id,
            right_dump_id=right_id,
        )
        self.compare_dump_worker.moveToThread(self.compare_dump_thread)

        self.compare_dump_thread.started.connect(self.compare_dump_worker.run)
        self.compare_dump_worker.finished.connect(self.compare_dump_thread.quit)
        self.compare_dump_worker.finished.connect(self.compare_dump_worker.deleteLater)
        self.compare_dump_thread.finished.connect(self.compare_dump_thread.deleteLater)

        logger.info(f"Started comparing dumps #{left_id} and #{right_id}")
        self.setAllControlsEnabled(False)
        self.compare_dump_thread.start()

        self.compare_dump_thread.finished.connect(lambda: self.populateDumpLists())
        self.compare_dump_thread.finished.connect(
            lambda: self.setAllControlsEnabled(True)
        )
        self.compare_dump_thread.finished.connect(
            lambda: logger.info("The dumps have been compared successfully")
        )

    # endregion

    def connectEvents(self):
        self.revealDBPushButton.clicked.connect(
            self.on_event_revealDBPushButton_clicked
        )
        self.addPushButton.clicked.connect(self.on_event_addPushButton_clicked)
        self.deletePushButton.clicked.connect(self.on_event_deletePushButton_clicked)
        self.comparePushButton.clicked.connect(self.on_event_comparePushButton_clicked)

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

    def setAllControlsEnabled(self, desired_state: bool = True) -> None:
        for button in (
            self.comparePushButton,
            self.deletePushButton,
            self.addPushButton,
            self.leftListView,
            self.rightListView,
            self.revealDBPushButton,
            self.dumpTitleLineEdit,
        ):
            button.setEnabled(desired_state)

    def getDumpIDfromListView(self, list_view: QListView) -> Optional[int]:
        item_val = list_view.currentIndex().data()

        if item_val == None:
            return None

        return int(re.search(r"(?<=#)\d+(?=\s)", item_val).group())

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
            QtGui.QIcon(os.path.join(RESOURCE_PATH, "ui", "icons", "favicon.png"))
        )
        self.setWindowTitle(f"deviceinfocompare v{deviceinfocompare.__version__}")

        # region Initializing error window
        self.err_msg = QMessageBox()
        self.err_msg.setIcon(QMessageBox.Icon.Critical)
        self.err_msg.setWindowTitle("Error")
        self.err_msg.setWindowIcon(
            QtGui.QIcon(
                os.path.join(RESOURCE_PATH, "ui", "icons", "exclamation-red.png")
            )
        )
        # endregion

        self.populateDumpLists()
        self.connectEvents()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_F1:
            webbrowser.open("https://github.com/alex-rusakevich/deviceinfocompare")
        elif (
            e.key() == Qt.Key.Key_F5
            and e.modifiers() == Qt.KeyboardModifier.AltModifier
        ):
            self.setWindowTitle("I ❤️❤️❤️ you! :D")


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()


def run_ui():
    window.show()
    app.exec()
