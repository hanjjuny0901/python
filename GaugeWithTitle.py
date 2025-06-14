import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from CircularGaugeWidget import (
    CircularGaugeWidget,  #        CircularGauge 클래스를 CircularGaugeWidget.py에서 임포트
)  # 첨부파일의 CircularGauge 클래스를 paste.py에 저장했다고 가정


class GaugeWithTitle(QWidget):
    def __init__(self, title="Circular Gauge"):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(0)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # 타이틀 라벨
        # self.title_label = QLabel(title)
        # self.title_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        # self.title_label.setStyleSheet(
        #     "color: white; font-size: 13px; font-weight: bold;"
        # )
        # layout.addWidget(self.title_label)

        # CircularGauge 위젯
        self.gauge = CircularGauge(title="", value=75)
        layout.addWidget(self.gauge, stretch=1)

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 다크 테마 팔레트 (첨부파일과 동일)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(40, 40, 40))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
    palette.setColor(QPalette.ToolTipBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(40, 40, 40))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    win = GaugeWithTitle("CPU 사용률")
    win.resize(400, 500)
    win.show()
    sys.exit(app.exec_())
