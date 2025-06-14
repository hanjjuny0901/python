import sys
import json
import psutil
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsLineItem,
    QMenu,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QColor, QPainter, QPalette
from SystemResourceModel import SystemResourceModel, TileModel
from SystemResourceViewModel import SystemResourceViewModel
from ResizableTileItem import ResizableTileItem
from CircularGaugeWidget import CircularGaugeWidget
from CPUGraphWidget import CPUGraphWidget
import qdarktheme
from typing import List
import os


class SystemResourceView(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setFrameShape(QGraphicsView.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setAttribute(Qt.WA_TranslucentBackground)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.viewport().installEventFilter(self)
        main_layout.addWidget(self.view)
        self.edit_mode = False
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.grid_size = 10
        self.tiles = []
        self.scene.setSceneRect(0, 0, 800, 600)
        self.model = SystemResourceModel()
        self.viewmodel = SystemResourceViewModel(self.model)
        self.viewmodel.cpu_data_updated.connect(self.on_cpu_data_updated)
        self.add_grid_lines()
        if self._has_saved_layout():
            self.load_layout()  # 저장된 레이아웃이 있으면 복구
        else:
            self.create_tiles()  # 없으면 기본 생성
        self.update_minimum_size()
        self.init_data_timer()
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
        # 예시: 9개 코어, 각 코어마다 CircularGauge/CPUGraphWidget 1개씩
        num_cores = 9
        core_ids = [f"core{i+1}" for i in range(num_cores)]
        widgets = []
        self.model.tiles.clear()
        self.tiles.clear()
        for idx, core_id in enumerate(core_ids):
            # CircularGauge 타일
            gauge_model = TileModel(
                x=10,
                y=10 + idx * 200,
                width=200,
                height=180,
                widget_type="CircularGauge",
                core_id=core_id,
            )
            self.model.add_tile(gauge_model)
            gauge = CircularGaugeWidget(core_id=core_id, viewmodel=self.viewmodel)
            gauge_tile = ResizableTileItem(
                self.grid_size,
                cols=10,
                rows=10,
                widget=gauge,
                color=QColor(80, 80, 80, 180),
                text=f"CPU {core_id}",
                all_tiles=self.tiles,
                tile_model=gauge_model,
            )
            gauge_tile.setRect(0, 0, gauge_model.width, gauge_model.height)
            gauge_tile.setPos(gauge_model.x, gauge_model.y)
            gauge_tile.viewmodel = self.viewmodel
            self.scene.addItem(gauge_tile)
            gauge_tile.set_enabled(self.edit_mode)
            self.tiles.append(gauge_tile)

            # CPUGraphWidget 타일
            graph_model = TileModel(
                x=220,
                y=10 + idx * 200,
                width=200,
                height=180,
                widget_type="CPUGraphWidget",
                core_id=core_id,
            )
            self.model.add_tile(graph_model)
            graph = CPUGraphWidget(core_id=core_id, viewmodel=self.viewmodel)
            graph_tile = ResizableTileItem(
                self.grid_size,
                cols=10,
                rows=10,
                widget=graph,
                color=QColor(80, 80, 80, 180),
                text=f"CPU {core_id}",
                all_tiles=self.tiles,
                tile_model=graph_model,
            )
            graph_tile.setRect(0, 0, graph_model.width, graph_model.height)
            graph_tile.setPos(graph_model.x, graph_model.y)
            graph_tile.viewmodel = self.viewmodel
            self.scene.addItem(graph_tile)
            graph_tile.set_enabled(self.edit_mode)
            self.tiles.append(graph_tile)

    def save_layout(self):
        state = self.model.to_dict()
        with open("dashboard_state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print("저장 완료: dashboard_state.json")

    def load_layout(self):
        try:
            with open("dashboard_state.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            # ✅ JSON 데이터를 모델에 주입
            self.model = SystemResourceModel.from_dict(data)
            self.viewmodel.model = self.model  # ViewModel 업데이트

            # 기존 타일 제거
            for tile in self.tiles:
                self.scene.removeItem(tile)
            self.tiles.clear()

            # 새 타일 생성
            for tile_model in self.model.tiles:
                if tile_model.widget_type == "CircularGaugeWidget":
                    widget = CircularGaugeWidget(
                        core_id=tile_model.core_id, viewmodel=self.viewmodel
                    )
                else:
                    widget = CPUGraphWidget(
                        core_id=tile_model.core_id, viewmodel=self.viewmodel
                    )

                tile = ResizableTileItem(
                    self.grid_size,
                    cols=10,
                    rows=10,
                    widget=widget,
                    color=QColor(80, 80, 80, 180),
                    text=f"CPU {tile_model.core_id}",
                    all_tiles=self.tiles,
                    tile_model=tile_model,
                )
                tile.setRect(0, 0, tile_model.width, tile_model.height)
                tile.setPos(tile_model.x, tile_model.y)
                tile._update_proxy_geometry()
                self.scene.addItem(tile)
                self.tiles.append(tile)

            # 씬 크기 조정
            if self.model.tiles:
                max_x = max(tile.x + tile.width for tile in self.model.tiles)
                max_y = max(tile.y + tile.height for tile in self.model.tiles)
                self.scene.setSceneRect(0, 0, max_x + 100, max_y + 100)

            self.edit_mode = data.get("edit_mode", False)
            self.update_grid_and_tiles()
            print("레이아웃 복구 성공")

        except Exception as e:
            print(f"레이아웃 복구 실패: {e}")
            self.create_tiles()  # 실패 시 기본 타일 생성

    def _has_saved_layout(self):
        return (
            os.path.exists("dashboard_state.json")
            and os.path.getsize("dashboard_state.json") > 0
        )

    def update_minimum_size(self):
        if not self.tiles:
            return
        max_right = max(tile.pos().x() + tile.rect().width() for tile in self.tiles)
        max_bottom = max(tile.pos().y() + tile.rect().height() for tile in self.tiles)
        margin = 20
        self.setMinimumSize(int(max_right + margin), int(max_bottom + margin))

    def init_data_timer(self):
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.fetch_cpu_data)
        self.data_timer.start(1000)  # 1초마다 업데이트

    def fetch_cpu_data(self):
        cpu_percent = psutil.cpu_percent(percpu=True)
        new_data = {f"core{i+1}": val for i, val in enumerate(cpu_percent)}
        self.viewmodel.update_cpu_values(new_data)

    def on_cpu_data_updated(self, new_data):
        # 이 메서드는 CircularGauge/CPUGraphWidget에서 ViewModel의 시그널로 자동 반영됨
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    window = SystemResourceView()
    window.show()
    sys.exit(app.exec_())
