import sys
import PyQt5.QtWidgets as QTw
from PyQt5.QtGui import QIcon


class MainWindow(QTw.QWidget):
    def __init__(self):
        self.app = QTw.QApplication(sys.argv)
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('Icon')

        self.show()

    def run(self):
        sys.exit(self.app.exec_())
