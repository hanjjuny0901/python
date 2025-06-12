import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsProxyWidget, QSizePolicy, QMenu
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPainterPath, QFont, QRegion

class CircularGauge(QWidget):
    def __init__(self, title="Circular Gauge", min_value=0.0, max_value=100.0, value=50.0, steps=1,
                 start_angle=-210.0, end_angle=30.0, outer_circle_pen_color=Qt.black,
                 outer_circle_brush_color=None, outer_circle_thickness=12,
                 inner_ring_pen_color=Qt.black, inner_ring_brush_color=Qt.white,
                 inner_circle_brush_color=None, number_font_size=10, number_font_family='Arial', parent=None):
        super().__init__(parent)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.steps = steps
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.angle_range = self.end_angle - self.start_angle
        self.outer_circle_thickness = outer_circle_thickness
        self.setMinimumSize(100, 100)
        self.outer_circle_pen_color = QColor(outer_circle_pen_color)
        self.outer_circle_brush_color = QColor(outer_circle_brush_color) if outer_circle_brush_color else None
        self.inner_ring_pen_color = QColor(inner_ring_pen_color)
        self.inner_ring_brush_color = QColor(inner_ring_brush_color) if inner_ring_brush_color else None
        self.inner_circle_brush_color = QColor(inner_circle_brush_color) if inner_circle_brush_color else None
        self.number_font_size = number_font_size
        self.number_font_family = number_font_family

    def setValue(self, value):
        self.value = max(self.min_value, min(self.max_value, value))
        self.update()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = self.rect()
            center = rect.center()
            # 타이틀을 더 위쪽에 표시
            painter.setPen(Qt.black)
            font = QFont(self.number_font_family, self.number_font_size)
            painter.setFont(font)
            title_rect = QRectF(rect.x(), rect.y() + 2, rect.width(), self.number_font_size * 2)
            painter.drawText(title_rect, Qt.AlignCenter, self.title if hasattr(self, 'title') else "Circular Gauge")
            radius = min(rect.width(), rect.height()) / 2 - self.outer_circle_thickness
            painter.translate(center)
            self.drawOuterArc(painter, radius)
            self.drawOuterArc2(painter, radius)
            self.drawCenterPercentage(painter, radius)
        except Exception as e:
            print(f"Error in paintEvent: {e}")

    def drawOuterArc(self, painter, radius):
        path = QPainterPath()
        outer_radius = radius
        inner_radius = radius - self.outer_circle_thickness
        total_angle = self.angle_range
        filled_angle = total_angle * (self.value / 100)
        green_limit = total_angle * 0.8
        yellow_limit = total_angle * 0.1
        red_limit = total_angle * 0.1
        green_angle = min(filled_angle, green_limit)
        yellow_angle = min(max(filled_angle - green_limit, 0), yellow_limit)
        red_angle = max(filled_angle - green_limit - yellow_limit, 0)
        current_start = -self.start_angle

        bg_path = QPainterPath()
        bg_rect = QRectF(-outer_radius, -outer_radius, 2*outer_radius, 2*outer_radius)
        bg_path.arcMoveTo(bg_rect, current_start)
        bg_path.arcTo(bg_rect, current_start, -total_angle)
        bg_path.lineTo(bg_path.currentPosition())
        inner_rect = QRectF(-inner_radius, -inner_radius, 2*inner_radius, 2*inner_radius)
        bg_path.arcTo(inner_rect, current_start - total_angle, total_angle)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(50, 50, 50, 100))
        painter.drawPath(bg_path)

        # 초록색 구간
        if green_angle > 0:
            green_path = QPainterPath()
            green_path.arcMoveTo(bg_rect, current_start)
            green_path.arcTo(bg_rect, current_start, -green_angle)
            green_path.lineTo(green_path.currentPosition())
            green_path.arcTo(inner_rect, current_start - green_angle, green_angle)
            painter.setBrush(QColor(0, 255, 0, 150))
            painter.drawPath(green_path)
            current_start -= green_angle

        # 노란색 구간
        if yellow_angle > 0:
            yellow_path = QPainterPath()
            yellow_path.arcMoveTo(bg_rect, current_start)
            yellow_path.arcTo(bg_rect, current_start, -yellow_angle)
            yellow_path.lineTo(yellow_path.currentPosition())
            yellow_path.arcTo(inner_rect, current_start - yellow_angle, yellow_angle)
            painter.setBrush(QColor(255, 255, 0, 150))
            painter.drawPath(yellow_path)
            current_start -= yellow_angle

        # 빨간색 구간
        if red_angle > 0:
            red_path = QPainterPath()
            red_path.arcMoveTo(bg_rect, current_start)
            red_path.arcTo(bg_rect, current_start, -red_angle)
            red_path.lineTo(red_path.currentPosition())
            red_path.arcTo(inner_rect, current_start - red_angle, red_angle)
            painter.setBrush(QColor(255, 0, 0, 150))
            painter.drawPath(red_path)

    def drawOuterArc2(self, painter, radius):
        outer_radius = radius + self.outer_circle_thickness/3 + 3
        inner_radius = radius + 3
        total_angle = self.angle_range
        green_angle = total_angle * 0.8
        yellow_angle = total_angle * 0.1
        red_angle = total_angle * 0.1
        start_angle = -self.start_angle

        # 초록색 아크 (0~80%)
        path_green = QPainterPath()
        rect = QRectF(-outer_radius, -outer_radius, 2*outer_radius, 2*outer_radius)
        path_green.arcMoveTo(rect, start_angle)
        path_green.arcTo(rect, start_angle, -green_angle)
        inner_rect = QRectF(-inner_radius, -inner_radius, 2*inner_radius, 2*inner_radius)
        path_green.lineTo(path_green.currentPosition())
        path_green.arcTo(inner_rect, start_angle - green_angle, green_angle)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 255, 0, 150))
        painter.drawPath(path_green)

        # 노란색 아크 (80~90%)
        path_yellow = QPainterPath()
        yellow_start = start_angle - green_angle
        path_yellow.arcMoveTo(rect, yellow_start)
        path_yellow.arcTo(rect, yellow_start, -yellow_angle)
        path_yellow.lineTo(path_yellow.currentPosition())
        path_yellow.arcTo(inner_rect, yellow_start - yellow_angle, yellow_angle)
        painter.setBrush(QColor(255, 255, 0, 150))
        painter.drawPath(path_yellow)

        # 빨간색 아크 (90~100%)
        path_red = QPainterPath()
        red_start = yellow_start - yellow_angle
        path_red.arcMoveTo(rect, red_start)
        path_red.arcTo(rect, red_start, -red_angle)
        path_red.lineTo(path_red.currentPosition())
        path_red.arcTo(inner_rect, red_start - red_angle, red_angle)
        painter.setBrush(QColor(255, 0, 0, 150))
        painter.drawPath(path_red)

    def drawCenterPercentage(self, painter, radius):
        painter.setPen(Qt.white)
        font = QFont()
        font.setPointSize(self.number_font_size)
        painter.setFont(font)
        text_rect = QRectF(-radius/2, -radius/2, radius, radius)
        painter.drawText(text_rect, Qt.AlignCenter, f"{self.value:.0f}%")

class ResizableTileItem(QGraphicsRectItem):
    def __init__(self, grid_size, cols, rows, widget, color, text, all_tiles=None, scene_rect=None):
        w = grid_size * cols
        h = grid_size * rows
        super().__init__(0, 0, w, h)
        self.grid_size = grid_size
        self.color = color
        self.setPen(QPen(Qt.NoPen))
        self.setFlags(QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.text = text
        self.resizing = False
        self.resize_handle_size = 30
        self.all_tiles = all_tiles or []
        self.proxy_inset = 10

        if scene_rect is None:
            scene = self.scene()
            self.scene_rect = scene.sceneRect() if scene else QRectF()
        else:
            self.scene_rect = scene_rect

        self.proxy = QGraphicsProxyWidget(self)
        self.proxy.setWidget(widget)
        self._update_proxy_geometry()

    def _update_proxy_geometry(self):
        tile_rect = self.rect()
        self.proxy.resize(int(tile_rect.width()), int(tile_rect.height()))
        self.proxy.setPos(0, 0)
        widget = self.proxy.widget()
        if widget:
            widget.resize(int(tile_rect.width()), int(tile_rect.height()))
            self.set_rounded_mask(widget, 0)

    def set_rounded_mask(self, widget, radius):
        rect = QRectF(widget.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        widget.setMask(region)

    def paint(self, painter, option, widget=None):
        rect = self.rect()
        corner_radius = 20
        path = QPainterPath()
        path.addRoundedRect(rect, corner_radius, corner_radius)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        painter.setPen(Qt.white)
        painter.drawText(rect.adjusted(0, 0, 0, -20), Qt.AlignBottom | Qt.AlignHCenter, self.text)

    def hoverMoveEvent(self, event):
        rect = self.rect().adjusted(0, 0, -1, -1)
        pos = event.pos()
        if (rect.right() - self.resize_handle_size <= pos.x() <= rect.right() and 
            rect.bottom() - self.resize_handle_size <= pos.y() <= rect.bottom()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        rect = self.rect()
        pos = event.pos()
        if (rect.right() - self.resize_handle_size <= pos.x() <= rect.right() and 
            rect.bottom() - self.resize_handle_size <= pos.y() <= rect.bottom()):
            self.resizing = True
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.resizing = False
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            new_width = round(event.pos().x() / self.grid_size) * self.grid_size
            new_height = round(event.pos().y() / self.grid_size) * self.grid_size
            new_width = max(self.grid_size, new_width)
            new_height = max(self.grid_size, new_height)

            old_rect = self.rect()
            self.setRect(0, 0, new_width, new_height)

            if self.is_within_scene() and not self.is_overlapping():
                self._update_proxy_geometry()
                widget = self.proxy.widget()
                widget.updateGeometry()
                widget.update()
                self.scene().update()
            else:
                self.setRect(0, 0, old_rect.width(), old_rect.height())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.resizing:
            if getattr(self, 'is_enabled', True):  # 편집모드일 때만 스냅
                final_pos = QPointF(
                    round(self.pos().x() / self.grid_size) * self.grid_size,
                    round(self.pos().y() / self.grid_size) * self.grid_size
                )
                self.setPos(final_pos)
        self.resizing = False
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def is_overlapping(self):
        my_rect = self.sceneBoundingRect()
        for tile in self.all_tiles:
            if tile is self:
                continue
            other_rect = tile.sceneBoundingRect()
            if (my_rect.left() < other_rect.right() and 
                my_rect.right() > other_rect.left() and 
                my_rect.top() < other_rect.bottom() and 
                my_rect.bottom() > other_rect.top()):
                return True
        return False

    def is_within_scene(self):
        tile_rect = self.sceneBoundingRect()
        return self.scene_rect.contains(tile_rect)

    def set_enabled(self, enabled):
        self.is_enabled = enabled
        self.setFlag(QGraphicsRectItem.ItemIsMovable, enabled)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, enabled)
        self.setAcceptHoverEvents(enabled)

    def get_state(self):
        """타일의 현재 상태(위치, 크기, 텍스트) 반환"""
        return {
            "x": float(self.pos().x()),
            "y": float(self.pos().y()),
            "width": float(self.rect().width()),
            "height": float(self.rect().height()),
            "text": self.text
        }

    def set_state(self, state):
        self.setRect(0, 0, state["width"], state["height"])
        self.setPos(state["x"], state["y"])
        self.text = state.get("text", self.text)
        self._update_proxy_geometry()

class SystemResourceView(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.viewport().installEventFilter(self)
        main_layout.addWidget(self.view)
        self.edit_mode = False
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.grid_size = 10
        self.tiles = []
        self.scene.setSceneRect(0, 0, 800, 600)
        self.add_grid_lines()
        self.create_tiles()
        self.load_layout()  # ✅ 앱 시작 시 자동 불러오기

    def eventFilter(self, obj, event):
        if obj is self.view.viewport() and event.type() == event.Resize:
            self.add_grid_lines()
        return super().eventFilter(obj, event)

    def add_grid_lines(self):
        for item in self.scene.items():
            if isinstance(item, QGraphicsLineItem):
                self.scene.removeItem(item)
        if self.edit_mode:
            viewport = self.view.viewport()
            width = viewport.width()
            height = viewport.height()
            self.scene.setSceneRect(0, 0, width, height)
            x = 0
            while x < width:
                line = QGraphicsLineItem(x, 0, x, height)
                line.setPen(QColor(200, 200, 200))
                self.scene.addItem(line)
                x += self.grid_size
            y = 0
            while y < height:
                line = QGraphicsLineItem(0, y, width, y)
                line.setPen(QColor(200, 200, 200))
                self.scene.addItem(line)
                y += self.grid_size

    def show_context_menu(self, pos):
        menu = QMenu()
        edit_action = menu.addAction("Edit Mode On" if not self.edit_mode else "Edit Mode Off")
        edit_action.triggered.connect(self.toggle_edit_mode)
        menu.addSeparator()
        save_action = menu.addAction("저장")
        save_action.triggered.connect(self.save_layout)
        load_action = menu.addAction("불러오기")
        load_action.triggered.connect(self.load_layout)
        menu.exec_(self.mapToGlobal(pos))

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        self.update_grid_and_tiles()

    def update_grid_and_tiles(self):
        self.add_grid_lines()
        for tile in self.tiles:
            tile.set_enabled(self.edit_mode)

    def create_tiles(self):
        widgets = [CircularGauge() for _ in range(9)]
        grid_cols = 3
        grid_rows = 3
        self.tiles.clear()
        for row in range(grid_rows):
            for col in range(grid_cols):
                idx = row * grid_cols + col
                x = col * self.grid_size * 10
                y = row * self.grid_size * 10
                tile = ResizableTileItem(
                    self.grid_size,
                    cols=10,
                    rows=10,
                    widget=widgets[idx],
                    color=QColor(60, 60, 150, 100),
                    text=f"Gauge {idx+1}",
                    all_tiles=self.tiles,
                    scene_rect=self.scene.sceneRect()
                )
                self.scene.addItem(tile)
                tile.setPos(x, y)
                tile.set_enabled(self.edit_mode)
                self.tiles.append(tile)

    def save_layout(self):
        state = {
            "edit_mode": self.edit_mode,
            "tiles": [tile.get_state() for tile in self.tiles]
        }
        with open("dashboard_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print("저장 완료: dashboard_state.json")

    def load_layout(self):
        try:
            with open("dashboard_state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
            tile_states = state.get("tiles", [])
            for tile, tile_state in zip(self.tiles, tile_states):
                tile.set_state(tile_state)
            self.edit_mode = state.get("edit_mode", False)
            self.update_grid_and_tiles()
            print("불러오기 완료: dashboard_state.json")
        except Exception as e:
            print(f"불러오기 실패: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemResourceView()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec_())
