import sys
import json
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsLineItem,
    QGraphicsProxyWidget,
    QSizePolicy,
    QMenu,
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPainterPath, QFont, QRegion

from GaugeWithTitle import (
    GaugeWithTitle,
)  # 첨부파일의 CircularGauge 클래스를 paste.py에 저장했다고 가정
import qdarktheme


class ResizableTileItem(QGraphicsRectItem):
    def __init__(
        self,
        grid_size,
        cols,
        rows,
        widget,
        color,
        text,
        all_tiles=None,
        scene_rect=None,
    ):
        w = grid_size * cols
        h = grid_size * rows
        super().__init__(0, 0, w, h)
        self.grid_size = grid_size
        self.color = color
        self.setPen(QPen(Qt.NoPen))
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemIsSelectable
            | QGraphicsRectItem.ItemSendsGeometryChanges
        )
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
            self.set_rounded_mask(widget, 20)

    def set_rounded_mask(self, widget, radius):
        rect = QRectF(widget.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        widget.setMask(region)

    def paint(self, painter, option, widget=None):
        rect = self.boundingRect()
        corner_radius = 20
        path = QPainterPath()
        path.addRoundedRect(rect, corner_radius, corner_radius)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self.color))
        # ✅ 테두리 추가
        painter.setPen(
            QPen(QColor(180, 180, 255, 180), 2)
        )  # 밝은 파란색 반투명, 두께 2
        painter.drawPath(path)
        # 내부 텍스트
        painter.setPen(Qt.white)
        painter.drawText(
            rect.adjusted(0, 0, 0, -20), Qt.AlignBottom | Qt.AlignHCenter, self.text
        )

    def boundingRect(self):
        # 테두리 두께(예: 5) 만큼 사방에 여유를 둠
        pen_width = 2  # 테두리 두께와 동일하게!
        adjust = pen_width / 2.0
        rect = super().boundingRect()
        return rect.adjusted(-adjust, -adjust, adjust, adjust)

    def hoverMoveEvent(self, event):
        rect = self.rect().adjusted(0, 0, -1, -1)
        pos = event.pos()
        if (
            rect.right() - self.resize_handle_size <= pos.x() <= rect.right()
            and rect.bottom() - self.resize_handle_size <= pos.y() <= rect.bottom()
        ):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        rect = self.rect()
        pos = event.pos()
        if (
            rect.right() - self.resize_handle_size <= pos.x() <= rect.right()
            and rect.bottom() - self.resize_handle_size <= pos.y() <= rect.bottom()
        ):
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
            if getattr(self, "is_enabled", True):  # 편집모드일 때만 스냅
                final_pos = QPointF(
                    round(self.pos().x() / self.grid_size) * self.grid_size,
                    round(self.pos().y() / self.grid_size) * self.grid_size,
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
            if (
                my_rect.left() < other_rect.right()
                and my_rect.right() > other_rect.left()
                and my_rect.top() < other_rect.bottom()
                and my_rect.bottom() > other_rect.top()
            ):
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
            "text": self.text,
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
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        main_layout.addWidget(self.view)
        self.edit_mode = False
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.grid_size = 10
        self.tiles = []
        # self.scene.setSceneRect(0, 0, 800, 600)
        self.add_grid_lines()
        self.create_tiles()
        self.load_layout()
        self.update_minimum_size()  # ✅ 앱 시작 시 자동 불러오기
        self.resize(
            int(self.scene.sceneRect().width()) + 10,
            int(self.scene.sceneRect().height()) + 10,
        )

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
        edit_action = menu.addAction(
            "Edit Mode On" if not self.edit_mode else "Edit Mode Off"
        )
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
        grid_cols = 3
        grid_rows = 3
        widgets = [
            GaugeWithTitle(f"CPU Usage {i+1}") for i in range(grid_cols * grid_rows)
        ]  # ✅ 타이틀 지정
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
                    scene_rect=self.scene.sceneRect(),
                )
                self.scene.addItem(tile)
                tile.setPos(x, y)
                tile.set_enabled(self.edit_mode)
                self.tiles.append(tile)

    def save_layout(self):
        state = {
            "edit_mode": self.edit_mode,
            "tiles": [tile.get_state() for tile in self.tiles],
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

    def update_minimum_size(self):
        """모든 타일의 경계까지 포함하는 최소 크기를 계산해 윈도우 최소 크기로 설정"""
        if not self.tiles:
            return
        max_right = max(tile.pos().x() + tile.rect().width() for tile in self.tiles)
        max_bottom = max(tile.pos().y() + tile.rect().height() for tile in self.tiles)
        margin = 20  # 스크롤바, 테두리 등 여유
        self.setMinimumSize(int(max_right + margin), int(max_bottom + margin))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    window = SystemResourceView()
    #  window.resize(900, 500)
    window.show()
    sys.exit(app.exec_())
