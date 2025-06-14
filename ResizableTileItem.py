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
    QGraphicsItem,
    QSizePolicy,
    QMenu,
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPainterPath, QFont, QRegion
from PyQt5.QtWidgets import QGraphicsSimpleTextItem
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from SystemResourceModel import SystemResourceModel
from SystemResourceViewModel import SystemResourceViewModel

from CircularGaugeWidget import CircularGaugeWidget  # CircularGaugeWidget
from GaugeWithTitle import GaugeWithTitle
from CPUGraphWidget import CPUGraphWidget
import qdarktheme
from SystemResourceModel import TileModel


class ResizableTileItem(QGraphicsRectItem):
    HANDLE_NONE = None
    HANDLE_RIGHT = "right"
    HANDLE_BOTTOM = "bottom"
    HANDLE_LEFT = "left"
    HANDLE_TOP = "top"
    HANDLE_BOTTOMRIGHT = "bottomright"
    HANDLE_BOTTOMLEFT = "bottomleft"
    HANDLE_TOPRIGHT = "topright"
    HANDLE_TOPLEFT = "topleft"

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
        border_width=2,
        corner_radius=10,
        tile_model: TileModel = None,
    ):
        w = grid_size * cols
        h = grid_size * rows
        super().__init__(0, 0, w, h)
        self.grid_size = grid_size
        self.color = color
        self.border_width = border_width
        self.corner_radius = corner_radius
        self.setPen(QPen(Qt.NoPen))
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemIsSelectable
            | QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.setFlag(QGraphicsItem.ItemHasNoContents, False)
        self.setOpacity(1.0)
        self.setAcceptHoverEvents(True)
        self.text = text
        self.resizing = False
        self.resize_handle_size = 10
        self.all_tiles = all_tiles or []
        self.tile_model = tile_model
        self.proxy_inset = 10
        self.resize_direction = self.HANDLE_NONE

        if scene_rect is None:
            scene = self.scene()
            self.scene_rect = scene.sceneRect() if scene else QRectF()
        else:
            self.scene_rect = scene_rect

        self.proxy = QGraphicsProxyWidget(self)
        self.proxy.setWidget(widget)
        self.proxy.setAcceptHoverEvents(False)  # 프록시 위젯이 hover 이벤트를 받지 않게
        self.setZValue(1)  # 타일이 ProxyWidget보다 위에 오도록
        self.proxy.setZValue(0)  # 프록시 위젯은 기본값(0)

        self.text_item = QGraphicsSimpleTextItem(self)
        self.text_item.setBrush(Qt.white)  # 텍스트 색상
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.text_item.setFont(font)
        self.text_item.setText(text)
        self.text_item.setZValue(2)  # ProxyWidget(0), 타일(1)보다 높게

        self._update_proxy_geometry()

    def _update_proxy_geometry(self):
        tile_rect = self.rect()
        # ✅ float → int 변환
        widget_width = int(tile_rect.width())
        widget_height = int(tile_rect.height())

        self.proxy.resize(widget_width, widget_height)
        self.proxy.setPos(0, 0)

        widget = self.proxy.widget()
        if widget:
            widget.resize(widget_width, widget_height)
            widget.updateGeometry()

        # 텍스트 위치 재조정
        text_rect = self.text_item.boundingRect()
        x = (tile_rect.width() - text_rect.width()) / 2
        y = 4
        self.text_item.setPos(x, y)

    def paint(self, painter, option, widget=None):
        rect = self.rect()
        corner_radius = self.corner_radius

        # 1. 타일 본체(배경)
        path = QPainterPath()
        path.addRoundedRect(rect, corner_radius, corner_radius)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawPath(path)

        # 2. 테두리
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(100, 100, 100, 180), self.border_width))
        painter.drawPath(path)

        # # 3. 텍스트
        # painter.setPen(Qt.white)
        # painter.drawText(
        #     rect.adjusted(0, 0, 0, -20), Qt.AlignBottom | Qt.AlignHCenter, self.text
        # )

        # 4. 선택 표시 (드래그/다중 선택 시)
        if self.isSelected():
            # 반투명 노란색 오버레이와 진한 테두리
            select_color = QColor(255, 215, 0, 80)  # 연한 노랑, 반투명
            painter.setBrush(select_color)
            painter.setPen(QPen(QColor(255, 200, 0), 4))  # 진한 노랑 테두리
            painter.drawPath(path)

        # 5. 핸들 감지 영역 시각화 (편집모드일 때만, 맨 마지막에!)
        if getattr(self, "is_enabled", False):  # 편집모드일 때만
            margin = self.resize_handle_size
            handle_color = QColor(0, 200, 255, 60)  # 밝은 시안, 반투명

            painter.setBrush(handle_color)
            painter.setPen(Qt.NoPen)
            # 네 모서리
            painter.drawRect(QRectF(rect.left(), rect.top(), margin, margin))  # 좌상
            painter.drawRect(
                QRectF(rect.right() - margin, rect.top(), margin, margin)
            )  # 우상
            painter.drawRect(
                QRectF(rect.left(), rect.bottom() - margin, margin, margin)
            )  # 좌하
            painter.drawRect(
                QRectF(rect.right() - margin, rect.bottom() - margin, margin, margin)
            )  # 우하
            # 네 변
            painter.drawRect(
                QRectF(
                    rect.left(), rect.top() + margin, margin, rect.height() - 2 * margin
                )
            )  # 좌변
            painter.drawRect(
                QRectF(
                    rect.right() - margin,
                    rect.top() + margin,
                    margin,
                    rect.height() - 2 * margin,
                )
            )  # 우변
            painter.drawRect(
                QRectF(
                    rect.left() + margin, rect.top(), rect.width() - 2 * margin, margin
                )
            )  # 상변
            painter.drawRect(
                QRectF(
                    rect.left() + margin,
                    rect.bottom() - margin,
                    rect.width() - 2 * margin,
                    margin,
                )
            )  # 하변

    def boundingRect(self):
        return super().boundingRect()  # 또는 self.rect()

    def hoverMoveEvent(self, event):
        rect = self.rect()  # 타일의 실제 영역 (테두리 포함 X)
        pos = event.pos()
        margin = self.resize_handle_size

        self.resize_direction = self.HANDLE_NONE

        # ✅ 경계 영역을 타일 내부로 한정
        # 왼쪽 위 모서리
        if (
            rect.left() <= pos.x() <= rect.left() + margin
            and rect.top() <= pos.y() <= rect.top() + margin
        ):
            self.setCursor(Qt.SizeFDiagCursor)
            self.resize_direction = self.HANDLE_TOPLEFT
        # 오른쪽 위 모서리
        elif (
            rect.right() - margin <= pos.x() <= rect.right()
            and rect.top() <= pos.y() <= rect.top() + margin
        ):
            self.setCursor(Qt.SizeBDiagCursor)
            self.resize_direction = self.HANDLE_TOPRIGHT
        # 왼쪽 아래 모서리
        elif (
            rect.left() <= pos.x() <= rect.left() + margin
            and rect.bottom() - margin <= pos.y() <= rect.bottom()
        ):
            self.setCursor(Qt.SizeBDiagCursor)
            self.resize_direction = self.HANDLE_BOTTOMLEFT
        # 오른쪽 아래 모서리
        elif (
            rect.right() - margin <= pos.x() <= rect.right()
            and rect.bottom() - margin <= pos.y() <= rect.bottom()
        ):
            self.setCursor(Qt.SizeFDiagCursor)
            self.resize_direction = self.HANDLE_BOTTOMRIGHT
        # 왼쪽 가장자리
        elif rect.left() <= pos.x() <= rect.left() + margin:
            self.setCursor(Qt.SizeHorCursor)
            self.resize_direction = self.HANDLE_LEFT
        # 오른쪽 가장자리
        elif rect.right() - margin <= pos.x() <= rect.right():
            self.setCursor(Qt.SizeHorCursor)
            self.resize_direction = self.HANDLE_RIGHT
        # 위쪽 가장자리
        elif rect.top() <= pos.y() <= rect.top() + margin:
            self.setCursor(Qt.SizeVerCursor)
            self.resize_direction = self.HANDLE_TOP
        # 아래쪽 가장자리
        elif rect.bottom() - margin <= pos.y() <= rect.bottom():
            self.setCursor(Qt.SizeVerCursor)
            self.resize_direction = self.HANDLE_BOTTOM
        else:
            self.setCursor(Qt.ArrowCursor)
            self.resize_direction = self.HANDLE_NONE

        super().hoverMoveEvent(event)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.rect())
        return path

    def mousePressEvent(self, event):
        if self.resize_direction and self.resize_direction != self.HANDLE_NONE:
            self.resizing = True
            self.resizing_direction = self.resize_direction
            self.resize_start_pos = event.pos()  # 아이템 기준 좌표
            self.resize_start_scene_pos = event.scenePos()  # ✅ 씬 기준 좌표 추가
            self.resize_start_rect = self.rect()
            self.original_scene_pos = self.pos()  # ✅ 초기 씬 위치 저장
        else:
            self.resizing = False
            self.resizing_direction = self.HANDLE_NONE
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing and self.resizing_direction:
            # ✅ 씬 좌표 기준 delta 계산
            delta_scene = event.scenePos() - self.resize_start_scene_pos
            dx = delta_scene.x()
            dy = delta_scene.y()

            rect = self.resize_start_rect
            min_size = self.grid_size
            new_x, new_y = self.original_scene_pos.x(), self.original_scene_pos.y()
            new_w, new_h = rect.width(), rect.height()

            # 각 핸들 방향별 처리
            if self.resizing_direction == self.HANDLE_RIGHT:
                new_w = max(min_size, rect.width() + dx)
                new_w = round(new_w / self.grid_size) * self.grid_size
                self.setRect(0, 0, new_w, rect.height())

            elif self.resizing_direction == self.HANDLE_BOTTOM:
                new_h = max(min_size, rect.height() + dy)
                new_h = round(new_h / self.grid_size) * self.grid_size
                self.setRect(0, 0, rect.width(), new_h)

            elif self.resizing_direction == self.HANDLE_LEFT:
                new_w = max(min_size, rect.width() - dx)
                new_x = self.original_scene_pos.x() + dx
                new_w = round(new_w / self.grid_size) * self.grid_size
                new_x = round(new_x / self.grid_size) * self.grid_size
                self.setRect(0, 0, new_w, rect.height())
                self.setPos(new_x, self.pos().y())

            elif self.resizing_direction == self.HANDLE_TOP:
                new_h = max(min_size, rect.height() - dy)
                new_y = self.original_scene_pos.y() + dy
                new_h = round(new_h / self.grid_size) * self.grid_size
                new_y = round(new_y / self.grid_size) * self.grid_size
                self.setRect(0, 0, rect.width(), new_h)
                self.setPos(self.pos().x(), new_y)

            elif self.resizing_direction == self.HANDLE_BOTTOMRIGHT:
                new_w = max(min_size, rect.width() + dx)
                new_h = max(min_size, rect.height() + dy)
                new_w = round(new_w / self.grid_size) * self.grid_size
                new_h = round(new_h / self.grid_size) * self.grid_size
                self.setRect(0, 0, new_w, new_h)

            elif self.resizing_direction == self.HANDLE_BOTTOMLEFT:
                new_w = max(min_size, rect.width() - dx)
                new_x = self.original_scene_pos.x() + dx
                new_h = max(min_size, rect.height() + dy)
                new_x = round(new_x / self.grid_size) * self.grid_size
                new_w = round(new_w / self.grid_size) * self.grid_size
                new_h = round(new_h / self.grid_size) * self.grid_size
                self.setRect(0, 0, new_w, new_h)
                self.setPos(new_x, self.pos().y())

            elif self.resizing_direction == self.HANDLE_TOPRIGHT:
                new_w = max(min_size, rect.width() + dx)
                new_h = max(min_size, rect.height() - dy)
                new_y = self.original_scene_pos.y() + dy
                new_w = round(new_w / self.grid_size) * self.grid_size
                new_h = round(new_h / self.grid_size) * self.grid_size
                new_y = round(new_y / self.grid_size) * self.grid_size
                self.setRect(0, 0, new_w, new_h)
                self.setPos(self.pos().x(), new_y)

            elif self.resizing_direction == self.HANDLE_TOPLEFT:
                new_w = max(min_size, rect.width() - dx)
                new_h = max(min_size, rect.height() - dy)
                new_x = self.original_scene_pos.x() + dx
                new_y = self.original_scene_pos.y() + dy
                new_x = round(new_x / self.grid_size) * self.grid_size
                new_y = round(new_y / self.grid_size) * self.grid_size
                new_w = round(new_w / self.grid_size) * self.grid_size
                new_h = round(new_h / self.grid_size) * self.grid_size
                self.setRect(0, 0, new_w, new_h)
                self.setPos(new_x, new_y)

            # 충돌 및 경계 체크
            if self.is_within_scene() and not self.is_overlapping():
                self._update_proxy_geometry()
                self.scene().update()
            else:
                self.setRect(0, 0, rect.width(), rect.height())
                self.setPos(self.original_scene_pos)

            return  # ✅ 기본 이동 동작 방지

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.resizing_direction = self.HANDLE_NONE
        self.setCursor(Qt.ArrowCursor)

        # ✅ 선택된 모든 타일 모델 업데이트
        scene = self.scene()
        if scene:
            selected_items = scene.selectedItems()
            for item in selected_items:
                if isinstance(item, ResizableTileItem):
                    item.tile_model.x = item.scenePos().x()
                    item.tile_model.y = item.scenePos().y()
                    item.tile_model.width = item.rect().width()
                    item.tile_model.height = item.rect().height()

        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # 그리드 스냅 적용
            new_pos = value
            snapped_x = round(new_pos.x() / self.grid_size) * self.grid_size
            snapped_y = round(new_pos.y() / self.grid_size) * self.grid_size
            return QPointF(snapped_x, snapped_y)
        return super().itemChange(change, value)

    def is_overlapping(self):
        my_rect = self.mapRectToScene(self.rect())  # ✅ 실제 rect를 씬 좌표로 변환
        for tile in self.all_tiles:
            if tile is self:
                continue
            other_rect = tile.mapRectToScene(tile.rect())
            if my_rect.intersects(other_rect):
                return True
        return False

    def is_within_scene(self):
        tile_rect = self.sceneBoundingRect()
        return self.scene().sceneRect().contains(tile_rect)

    def set_enabled(self, enabled):
        self.is_enabled = enabled
        self.setFlag(QGraphicsRectItem.ItemIsMovable, enabled)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, enabled)
        self.setAcceptHoverEvents(enabled)
        self.proxy.setAcceptHoverEvents(not enabled)

        widget = self.proxy.widget()
        if widget:
            # ✅ CPUGraphWidget의 모든 마우스 이벤트 차단
            widget.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)
            widget.setMouseTracking(False)
            widget.setFocusPolicy(Qt.NoFocus)

            # Matplotlib Figure의 이벤트도 차단
            canvas = widget.findChild(FigureCanvas)
            if canvas:
                canvas.setAttribute(Qt.WA_TransparentForMouseEvents, enabled)
                canvas.setFocusPolicy(Qt.NoFocus)

    def get_state(self):
        if hasattr(self, "viewmodel"):
            self.viewmodel.set_pos(self.scenePos().x(), self.scenePos().y())
            self.viewmodel.set_size(self.rect().width(), self.rect().height())
            self.viewmodel.set_text(self.text)
            return self.viewmodel.model.to_dict()
        else:
            # fallback
            scene_pos = self.scenePos()
            return {
                "x": float(scene_pos.x()),
                "y": float(scene_pos.y()),
                "width": float(self.rect().width()),
                "height": float(self.rect().height()),
                "text": self.text,
            }

    def set_state(self, state):
        if hasattr(self, "viewmodel"):
            self.viewmodel.model = SystemResourceModel.from_dict(state)
            self.setRect(
                0, 0, self.viewmodel.get_size()[0], self.viewmodel.get_size()[1]
            )
            self.setPos(self.viewmodel.get_pos()[0], self.viewmodel.get_pos()[1])
            self.text = self.viewmodel.get_text()
            self.text_item.setText(self.text)
            self._update_proxy_geometry()
        else:
            # fallback
            self.setRect(0, 0, int(state["width"]), int(state["height"]))
            self.setPos(state["x"], state["y"])
            self.text = state.get("text", self.text)
            self.text_item.setText(self.text)
            self._update_proxy_geometry()
