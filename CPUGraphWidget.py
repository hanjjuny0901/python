import sys
import psutil
import numpy as np
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import qdarktheme


class CPUGraphWidget(QWidget):
    def __init__(self, title="CPU Usage", num_points=60, parent=None):
        super().__init__(parent)
        self.num_points = num_points
        self.data = [0] * num_points

        # Matplotlib Figure 설정
        self.figure = Figure(figsize=(5, 3), facecolor="#2e2e2e")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

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
        self.ax.set_xlim(0, 60)
        self.ax.set_ylim(0, 100)
        self.ax.set_xticks(range(0, 61, 10))
        self.ax.set_yticks([0, 20, 40, 60, 80, 100])
        self.ax.set_autoscale_on(False)
        self.ax.set_title(title)
        self.ax.set_xlabel("Time (seconds)")
        self.ax.set_ylabel("Usage (%)")
        self.ax.grid(True, color="gray", linestyle="--", linewidth=0.5, alpha=0.7)

        # 초기 플롯 생성
        (self.line,) = self.ax.plot(range(num_points), self.data, color="#00FF00")
        self.fill = self.ax.fill_between(  # ✅ 채움 영역 추가
            range(num_points), self.data, 0, color="#00FF00", alpha=0.3
        )

        # 레이아웃
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # 타이머 설정
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1000)

    def update_graph(self):
        cpu_percent = psutil.cpu_percent()
        self.data.pop(0)
        self.data.append(cpu_percent)

        # 라인 업데이트
        self.line.set_ydata(self.data)

        # 채움 영역 업데이트
        x = np.arange(len(self.data))
        y = self.data
        verts = np.vstack(
            [np.column_stack((x, y)), np.column_stack((x[::-1], np.zeros_like(x)))]
        )
        self.fill.set_verts([verts])  # ✅ 채움 영역 갱신

        self.canvas.draw_idle()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")

    widget = CPUGraphWidget("CPU Usage")
    widget.resize(600, 350)
    widget.show()
    sys.exit(app.exec_())
