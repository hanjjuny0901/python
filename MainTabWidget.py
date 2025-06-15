from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget, QVBoxLayout
import sys
from SystemResourceView import SystemResourceView
import qdarktheme
from PyQt5.QtCore import pyqtSignal
import json


class MainTabWidget(QTabWidget):
    current_profile_changed = pyqtSignal(str)  # ✅ 프로필 변경 신호

    def __init__(self):
        super().__init__()
        self.current_profile = "ALL"  # 모든 탭이 공유하는 프로필
        self._views = []  # 모든 SystemResourceView 인스턴스 저장
        self._load_current_profile()  # 앱 시작 시 프로필 불러오기

        # 각 시스템별 리소스 뷰를 탭으로 추가
        self.ap1_view = SystemResourceView(system_name="AP1", parent=self)
        self.addTab(self.ap1_view, "AP1")
        self._views.append(self.ap1_view)

        self.ap2_view = SystemResourceView(system_name="AP2", parent=self)
        self.addTab(self.ap2_view, "AP2")
        self._views.append(self.ap2_view)

        self.mcu_view = SystemResourceView(system_name="MCU", parent=self)
        self.addTab(self.mcu_view, "MCU")
        self._views.append(self.mcu_view)

        # ✅ 프로필 변경 시 모든 뷰 업데이트
        self.current_profile_changed.connect(self._broadcast_profile_change)

    def _broadcast_profile_change(self, profile_name):
        for idx in range(self.count()):
            tab = self.widget(idx)
            if hasattr(tab, "change_profile"):
                tab.change_profile(profile_name)

    def set_profile(self, profile_name: str):
        """프로필 변경 메서드 (신호 발생만 담당)"""
        if self.current_profile != profile_name:
            self.current_profile = profile_name
            self.current_profile_changed.emit(profile_name)
            self._save_current_profile()

    def _save_current_profile(self):
        """전역 프로필 저장"""
        config = {"last_profile": self.current_profile}
        with open("app_config.json", "w") as f:
            json.dump(config, f)

    def _load_current_profile(self):
        """저장된 전역 프로필 불러오기"""
        try:
            with open("app_config.json", "r") as f:
                config = json.load(f)
                self.current_profile = config.get("last_profile", "ALL")
        except:
            self.current_profile = "ALL"
        self.current_profile_changed.emit(self.current_profile)  # 모든 탭에 적용


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    window = MainTabWidget()
    window.setWindowTitle("System Resource Dashboard")
    window.show()
    sys.exit(app.exec_())
