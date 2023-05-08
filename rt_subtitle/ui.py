import logging
import os
import sys
from threading import Thread
import time

from PyQt6 import QtWidgets
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.uic.load_ui import loadUi

from .manager import Manager
from .recognize import Recorder

BASE_DIR = os.path.dirname(__file__)
sys.path.append(BASE_DIR)
USER_DIR = os.path.expanduser("~")


class MainWindow:

    def __init__(self) -> None:
        self.manager = None
        self.is_task_started = False
        self.model_path = os.path.join(USER_DIR, 'test/subtitle/paddlespeech_stream')

        self.ui = loadUi(os.path.join(BASE_DIR, "main.ui"))
        self.ui.gridLayout.setVerticalSpacing(20)

        conf = self._read_config()
        self.ui.per_v.setValue(conf["per"])
        self.ui.freq_v.setValue(conf["freq"])
        self.ui.mini.setChecked(True if conf["mini"] else False)

        self.ui.per_v.valueChanged.connect(self._on_per_v_value_changed)
        self.ui.freq_v.valueChanged.connect(self._on_freq_v_value_changed)

        self.ui.source.addItems(Recorder.get_all_source())
        self.ui.source.setCurrentIndex(0)
        self.ui.source.clicked.connect(self._on_source_clicked)
        self.ui.source.currentTextChanged.connect(
            self._on_source_current_text_changed)

        self.ui.start.clicked.connect(self._on_start_clicked)

        self.ui.on_close.connect(self._handle_quit)

        self.float_ui = loadUi(os.path.join(BASE_DIR, "floatWin.ui"))
        self.float_ui.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.float_ui.setStyleSheet("""
QLabel {
background-color: #cc808080;
border-radius: 10px;
padding: 4px;
color: white;
}
""")

        self.ui.show()

    def _read_config(self) -> dict:
        per = 0.5
        freq = 6
        mini = 1
        conf_path = os.path.join(USER_DIR, "/.cache/rtsubtitle.conf")
        if os.path.exists(conf_path):
            try:
                with open(conf_path, "r", encoding="UTF-8") as fp:
                    data = fp.readlines()
                per = float(data[0])
                freq = int(data[1])
                mini = int(data[2])
            except Exception as e:
                logging.error(e)
        return {"per": per, "freq": freq, "mini": mini}

    def _write_config(self):
        pass

    def _on_per_v_value_changed(self):
        if not self.manager:
            return
        self.manager.per_record_second = self.ui.per_v.value()

    def _on_freq_v_value_changed(self):
        if not self.manager:
            return
        self.manager.reco_nums = self.ui.freq_v.value()

    def _on_source_clicked(self):
        self.ui.source.clear()
        self.ui.source.addItems(Recorder.get_all_source())

    def _on_source_current_text_changed(self):
        if not self.manager:
            return
        self.manager.switch_source(self.ui.source.currentText())

    def start_task(self):
        if not self.manager:
            self.manager = Manager(self.ui.per_v.value(),
                                   self.ui.freq_v.value(), self.model_path,
                                   self.ui.source.currentText())
            self.manager.run()
        else:
            if self.manager.is_running:
                return
            else:
                self.manager.run()
        Thread(target=self.result_update, daemon=True).start()

    def stop_task(self):
        if self.manager and self.manager.is_running:
            self.manager.stop()

    def result_update(self):
        while self.is_task_started:
            result = self.manager.last_result + self.manager.current_result
            self.float_ui.resultText.setText(result)
            self.float_ui.resultText.update()
            time.sleep(0.3)

    def create_float_window(self):
        if self.ui.mini.isChecked():
            self.ui.showMinimized()
        cp = QtGui.QGuiApplication.primaryScreen().availableGeometry().center()
        self.float_ui.move(int(cp.x() - self.float_ui.width() / 2),
                           int(1.8 * cp.y()))
        self.float_ui.show()

    def destroy_float_window(self):
        self.float_ui.close()

    def _on_start_clicked(self):
        self.is_task_started = not self.is_task_started
        if self.is_task_started:
            self.ui.start.setText("停止识别")
            self.ui.start.setEnabled(False)
            self.start_task()
            self.create_float_window()
            self.ui.start.setEnabled(True)
        else:
            self.ui.start.setText("开始识别")
            self.ui.start.setEnabled(False)
            self.stop_task()
            self.destroy_float_window()
            self.ui.start.setEnabled(True)

    def _handle_quit(self):
        if self.is_task_started:
            self._on_start_clicked()
        if self.manager:
            self.manager.destroy()
        self._write_config()
        self.ui.close()

    @classmethod
    def get_theme(cls) -> str:
        themes = QtWidgets.QStyleFactory.keys()
        f_themes = list(filter(lambda x: "dark" not in x, themes))
        if len(f_themes):
            return f_themes[0]
        else:
            return themes[0]
