import sys
from PyQt5.QtWidgets import QApplication, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPainterPath, QFont, QPalette
from typing import Optional
from SystemResourceViewModel import SystemResourceViewModel  # ViewModel 임포트


class CircularGaugeWidget(QWidget):
    def __init__(
        self,
        core_id: str,  # ✅ core_id 추가
        viewmodel: SystemResourceViewModel,  # ✅ viewmodel 추가
        title: Optional[str] = None,
        min_value: float = 0.0,
        max_value: float = 100.0,
        steps: int = 1,
        start_angle: float = -210.0,
        end_angle: float = 30.0,
        outer_circle_pen_color=QColor(50, 50, 50),
        outer_circle_brush_color=QColor(30, 30, 30),
        outer_circle_thickness=12,
        inner_ring_pen_color=QColor(70, 70, 70),
        inner_ring_brush_color=QColor(40, 40, 40),
        inner_circle_brush_color=QColor(20, 20, 20),
        number_font_size=10,
        number_font_family="Arial",
        parent=None,
    ):
        super().__init__(parent)
        self.core_id = core_id  # ✅ core_id 저장
        self.viewmodel = viewmodel  # ✅ viewmodel 저장

        # ✅ title이 없으면 core_id 기반으로 자동 생성
        self.title = title if title else f"CPU {core_id}"

        self.min_value = min_value
        self.max_value = max_value
        self.value = 0.0  # ✅ 초기값 0으로 설정 (ViewModel에서 업데이트)
        self.steps = steps
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.angle_range = self.end_angle - self.start_angle
        self.outer_circle_thickness = outer_circle_thickness
        self.setMinimumSize(100, 100)
        self.outer_circle_pen_color = outer_circle_pen_color
        self.outer_circle_brush_color = outer_circle_brush_color
        self.inner_ring_pen_color = inner_ring_pen_color
        self.inner_ring_brush_color = inner_ring_brush_color
        self.inner_circle_brush_color = inner_circle_brush_color
        self.number_font_size = number_font_size
        self.number_font_family = number_font_family
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # ✅ ViewModel의 데이터 업데이트 신호 연결
        self.viewmodel.cpu_data_updated.connect(self.on_cpu_updated)

    def on_cpu_updated(self, new_data: dict):
        """ViewModel에서 CPU 데이터 업데이트 시 호출"""
        if self.core_id in new_data:
            self.setValue(new_data[self.core_id])

    def setValue(self, value):
        self.value = max(self.min_value, min(self.max_value, value))
        self.update()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = self.rect()

            # ✅ 타일 높이의 20%를 상단 여백으로 사용 (동적 계산)
            top_margin = int(rect.height() * 0.2)
            content_rect = rect.adjusted(0, top_margin, 0, 0)

            # ✅ 콘텐츠 영역 기반으로 반지름 계산
            center = content_rect.center()
            radius = (content_rect.height() - 20) // 2  # 20px 패딩

            # ✅ 동적으로 두께 계산 (반지름의 20%, 최소 5px)
            self.outer_circle_thickness = max(5, int(radius * 0.3))

            painter.translate(center)
            self.drawInnerArc(painter, radius)
            self.drawOuterArc(painter, radius)
            self.drawCenterPercentage(painter, radius)
        except Exception as e:
            print(f"Error in paintEvent: {e}")

    def drawInnerArc(self, painter, radius):
        path = QPainterPath()
        outer_radius = radius
        inner_radius = radius - self.outer_circle_thickness
        total_angle = self.angle_range
        filled_angle = total_angle * (self.value / 100)

        # 구간별 색상 결정 (80% 초록, 80~90% 노랑, 90% 이상 빨강)
        if self.value <= 80:
            color = QColor(0, 200, 0, 180)  # 초록
        elif 80 < self.value <= 90:
            color = QColor(220, 200, 0, 180)  # 노랑
        else:
            color = QColor(220, 50, 50, 200)  # 빨강

        # 단일 아크 생성
        path.arcMoveTo(
            QRectF(-outer_radius, -outer_radius, 2 * outer_radius, 2 * outer_radius),
            -self.start_angle,
        )
        path.arcTo(
            QRectF(-outer_radius, -outer_radius, 2 * outer_radius, 2 * outer_radius),
            -self.start_angle,
            -filled_angle,
        )
        path.lineTo(path.currentPosition())
        path.arcTo(
            QRectF(-inner_radius, -inner_radius, 2 * inner_radius, 2 * inner_radius),
            -self.start_angle - filled_angle,
            filled_angle,
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawPath(path)

    def drawOuterArc(self, painter, radius):
        outer_radius = radius + self.outer_circle_thickness / 3 + 3
        inner_radius = radius + 3
        total_angle = self.angle_range
        green_angle = total_angle * 0.8
        yellow_angle = total_angle * 0.1
        red_angle = total_angle * 0.1
        start_angle = -self.start_angle

        # 초록색 아크 (0~80%)
        path_green = QPainterPath()
        rect = QRectF(-outer_radius, -outer_radius, 2 * outer_radius, 2 * outer_radius)
        path_green.arcMoveTo(rect, start_angle)
        path_green.arcTo(rect, start_angle, -green_angle)
        inner_rect = QRectF(
            -inner_radius, -inner_radius, 2 * inner_radius, 2 * inner_radius
        )
        path_green.lineTo(path_green.currentPosition())
        path_green.arcTo(inner_rect, start_angle - green_angle, green_angle)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 200, 0, 100))
        painter.drawPath(path_green)

        # 노란색 아크 (80~90%)
        path_yellow = QPainterPath()
        yellow_start = start_angle - green_angle
        path_yellow.arcMoveTo(rect, yellow_start)
        path_yellow.arcTo(rect, yellow_start, -yellow_angle)
        path_yellow.lineTo(path_yellow.currentPosition())
        path_yellow.arcTo(inner_rect, yellow_start - yellow_angle, yellow_angle)
        painter.setBrush(QColor(220, 200, 0, 100))
        painter.drawPath(path_yellow)

        # 빨간색 아크 (90~100%)
        path_red = QPainterPath()
        red_start = yellow_start - yellow_angle
        path_red.arcMoveTo(rect, red_start)
        path_red.arcTo(rect, red_start, -red_angle)
        path_red.lineTo(path_red.currentPosition())
        path_red.arcTo(inner_rect, red_start - red_angle, red_angle)
        painter.setBrush(QColor(220, 50, 50, 120))
        painter.drawPath(path_red)

    def drawTitle(self, painter, rect, radius, center):
        painter.setPen(Qt.white)
        font = QFont(self.number_font_family, self.number_font_size)
        painter.setFont(font)
        # 게이지 원의 윗부분 위에 타이틀을 놓음
        # center.y() - radius가 원의 맨 위, 거기서 약간 위로 띄움
        title_y = center.y() - radius - 30 - self.number_font_size * 1.2
        title_rect = QRectF(rect.x(), title_y, rect.width(), self.number_font_size * 2)
        painter.drawText(
            title_rect,
            Qt.AlignCenter,
            self.title if hasattr(self, "title") else "Circular Gauge",
        )

    def drawCenterPercentage(self, painter, radius):
        if self.value <= 80:
            color = QColor(0, 200, 0, 180)  # 초록
        elif 80 < self.value <= 90:
            color = QColor(220, 200, 0, 180)  # 노랑
        else:
            color = QColor(220, 50, 50, 200)  # 빨강
        painter.setPen(color)
        # 폰트 크기를 위젯 크기에 맞게 동적으로 계산
        percent_font_size = max(10, int(radius * 0.2))  # 더 크게!
        font = QFont(self.number_font_family, percent_font_size)
        painter.setFont(font)
        # 사각형을 충분히 크게 (중앙 정렬)
        box_size = radius * 1.6  # 1.6~1.8 정도로 확대
        text_rect = QRectF(-box_size / 2, -box_size / 2, box_size, box_size)
        painter.drawText(text_rect, Qt.AlignCenter, f"{self.value:.0f}%")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 전체 다크 테마 팔레트 적용
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

    gauge = CircularGauge(
        title="Circular Gauge",
        value=75,
        steps=5,
        outer_circle_pen_color=QColor(50, 50, 50),
        outer_circle_brush_color=QColor(30, 30, 30),
        inner_ring_pen_color=QColor(70, 70, 70),
        inner_ring_brush_color=QColor(40, 40, 40),
        inner_circle_brush_color=QColor(20, 20, 20),
        number_font_size=14,
        number_font_family="Arial",
    )
    gauge.resize(400, 400)
    gauge.show()
    sys.exit(app.exec_())
