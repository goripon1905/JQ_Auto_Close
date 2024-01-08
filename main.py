import sys
import json
import time
import pygetwindow as gw
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal

target_window_title = "JQuake"
config_file = "config.json"

def load_config():
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        return {"timeout_seconds": 10, "error": f"設定ファイル'{config_file}'が見つかりません。デフォルトタイムアウト設定(10)を使用します。", "auto_start": False}
    except json.JSONDecodeError:
        return {"timeout_seconds": 10, "error": f"設定ファイル'{config_file}'の解析に失敗しました。デフォルトタイムアウト設定(10)を使用します。", "auto_start": False}

class MonitoringThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._isRunning = True

    def run(self):
        while self._isRunning:
            target_window = gw.getWindowsWithTitle(target_window_title)
            if len(target_window) > 0:
                if target_window[0].isMinimized:
                    self.log_signal.emit(time.strftime("%H:%M:%S [info] 待機中です", time.localtime()))
                else:
                    self.log_signal.emit(time.strftime("%H:%M:%S [info] JQuakeの最小化が解除されました", time.localtime()))
                    for i in range(self.config["timeout_seconds"], 0, -1):
                        time.sleep(1)
                        if not self._isRunning:
                            return
                        self.log_signal.emit(time.strftime(f"%H:%M:%S [info] {i}秒後に最小化します", time.localtime()))
                    target_window[0].minimize()
                    self.log_signal.emit(time.strftime("%H:%M:%S [info] JQuakeを最小化しました", time.localtime()))
            else:
                self.log_signal.emit(time.strftime("%H:%M:%S [info] 待機中です", time.localtime()))
            time.sleep(1)
    
    def stop(self):
        self._isRunning = False

class WindowApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.status_label = QLabel("JQuake自動最小化ツール by goripon1905\n-ログ-")
        layout.addWidget(self.status_label)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        layout.addWidget(self.log_text_edit)

        self.start_btn = QPushButton('監視を開始', self)
        self.start_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton('監視を終了', self)
        self.stop_btn.clicked.connect(self.close_app)
        self.stop_btn.setEnabled(False) 
        layout.addWidget(self.stop_btn)

        self.setLayout(layout)
        self.setWindowTitle('JQ自動最小化ツール')

        self.monitoring_thread = None

    def update_log(self, message):
        self.log_text_edit.append(message)

    def start_monitoring(self):
        config = load_config()
        self.monitoring_thread = MonitoringThread(config)
        self.monitoring_thread.log_signal.connect(self.update_log)
        self.monitoring_thread.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.update_log("監視を開始しました...")

    def close_app(self):
        if self.monitoring_thread is not None:
            self.monitoring_thread.stop()
            self.monitoring_thread.wait()
        self.update_log("アプリケーションを終了します...")
        self.close()

    def auto_start_monitoring(self):
        config = load_config()
        if config.get("auto_start", False):
            self.start_monitoring()

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('library/ico.ico'))
    ex = WindowApp()
    ex.show()
    ex.auto_start_monitoring()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
