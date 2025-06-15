from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import psutil
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from SystemResourceViewModel import SystemResourceViewModel  # ✅ ViewModel import 추가


class CPUGraphWidget(QWidget):
    def __init__(
        self,
        core_id: str = None,  # ✅ core_id 추가
        viewmodel: SystemResourceViewModel = None,  # ✅ viewmodel 추가
        title: str = "CPU Usage",
        num_points: int = 30,
        parent=None,
    ):
        super().__init__(parent)
        self.core_id = core_id  # ✅ core_id 저장
        self.viewmodel = viewmodel  # ✅ viewmodel 저장
        self.num_points = num_points
        self.data = [0] * num_points

        # ✅ title이 없으면 core_id 기반으로 자동 생성
        if core_id and not title:
            self.title = f"CPU {core_id} Usage"
        else:
            self.title = title

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("background: transparent;")

        # 200x200 픽셀로 지정 (dpi=100, figsize=2x2인치)
        self.figure = Figure(figsize=(2, 2), dpi=80, facecolor="#2e2e2e")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        # ✅ 서브플롯 여백 최소화
        self.figure.subplots_adjust(
            left=0.12,   # 좌측 여백 12%
            right=0.95,  # 우측 여백 2%
            bottom=0.15, # 하단 여백 15%
            top=0.9      # 상단 여백 10%
        )

        # 그래프 스타일 설정
        self.ax.set_facecolor("#2e2e2e")
        self.ax.tick_params(axis="both", colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")
        self.ax.spines["bottom"].set_color("white")
        self.ax.spines["top"].set_color("white")
        self.ax.spines["left"].set_color("white")
        self.ax.spines["right"].set_color("white")

        # 축 범위 및 tick 설정
        self.ax.set_xlim(0, 30)
        self.ax.set_ylim(0, 100)
        self.ax.set_xticks(range(0, 31, 10))
        self.ax.set_yticks([0, 25, 50, 75, 100])
        self.ax.set_autoscale_on(False)
        self.ax.set_xlabel("Time (seconds)")
        self.ax.set_ylabel("Usage (%)")
        self.ax.grid(True, color="gray", linestyle="--", linewidth=0.4, alpha=0.7)
        self.ax.tick_params(
            axis="both", which="major", labelsize=7
        )  # ✅ 폰트 크기 축소

        # 초기 플롯 생성
        (self.line,) = self.ax.plot(range(num_points), self.data, color="#00FF00")
        self.fill = self.ax.fill_between(
            range(num_points), self.data, 0, color="#00FF00", alpha=0.3
        )

        # 레이아웃
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # ✅ 여백 제거
        layout.setSpacing(0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # ✅ ViewModel 연결 (편집모드가 아닐 때만 타이머 사용)
        if self.viewmodel and self.core_id:
            self.viewmodel.cpu_data_updated.connect(self.on_cpu_updated)
        else:
            # ✅ ViewModel이 없는 경우 기존 타이머 유지 (테스트용)
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_graph)
            self.timer.start(1000)

    # def resizeEvent(self, event):
    #     """위젯 크기 변경 시 Figure 크기 동기화"""
    #     super().resizeEvent(event)
    #     width_inch = self.width() / self.figure.dpi
    #     height_inch = self.height() / self.figure.dpi
    #     self.figure.set_size_inches(width_inch, height_inch)
    #     self.canvas.draw()
        
    def on_cpu_updated(self, new_data: dict):
        """ViewModel에서 CPU 데이터 업데이트 시 호출"""
        if self.core_id and self.core_id in new_data:
            cpu_value = new_data[self.core_id]
            self.update_graph(cpu_value)

    def update_graph(self, cpu_value: float = None):
        """외부에서 값을 전달받거나 psutil로 직접 측정"""
        # ✅ 값이 없으면 psutil로 측정 (테스트용)
        if cpu_value is None:
            cpu_value = psutil.cpu_percent()

        self.data.pop(0)
        self.data.append(cpu_value)
        self.line.set_ydata(self.data)

        # 채움 영역 업데이트
        x = np.arange(len(self.data))
        y = self.data
        verts = np.vstack(
            [np.column_stack((x, y)), np.column_stack((x[::-1], np.zeros_like(x)))]
        )
        self.fill.set_verts([verts])
        self.canvas.draw_idle()


# 테스트 코드
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    import qdarktheme

    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")

    # ✅ ViewModel과 연동 테스트
    from SystemResourceModel import SystemResourceModel
    from SystemResourceViewModel import SystemResourceViewModel

    model = SystemResourceModel()
    viewmodel = SystemResourceViewModel(model)

    widget = CPUGraphWidget(
        core_id="core1", viewmodel=viewmodel, title="Custom CPU Usage"
    )
    widget.resize(200, 200)
    widget.show()

    # 테스트 데이터 전송 (ViewModel 시뮬레이션)
    test_timer = QTimer()
    test_timer.timeout.connect(
        lambda: viewmodel.update_cpu_values({"core1": np.random.randint(0, 100)})
    )
    test_timer.start(1000)

    sys.exit(app.exec_())
