from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget, QVBoxLayout
import sys
from SystemResourceView import SystemResourceView
import qdarktheme


class MainTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        # 각 시스템별 리소스 뷰를 탭으로 추가
        self.ap1_view = SystemResourceView(system_name="AP1")
        self.addTab(self.ap1_view, "AP1")

        self.ap2_view = SystemResourceView(system_name="AP2")
        self.addTab(self.ap2_view, "AP2")

        self.mcu_view = SystemResourceView(system_name="MCU")
        self.addTab(self.mcu_view, "MCU")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    window = MainTabWidget()
    window.setWindowTitle("System Resource Dashboard")
    window.show()
    sys.exit(app.exec_())
