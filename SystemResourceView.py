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
    QSizePolicy,
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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainTabWidget import MainTabWidget


class ColorDemoWidget(QWidget):
    def __init__(self, color=QColor(255, 100, 100, 180), parent=None):
        super().__init__(parent)
        self.color = color
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())


class SystemResourceView(QWidget):
    def __init__(self, system_name: str, parent: "MainTabWidget"):
        super().__init__()
        self.system_name = system_name
        self.current_profile = "ALL"  # 기본 프로필
        self.parent_tab = parent

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
        self.grid_size = 10
        self.tiles = []
        self.scene.setSceneRect(0, 0, 600, 600)
        self.model = SystemResourceModel()
        self.viewmodel = SystemResourceViewModel(self.model)
        self.viewmodel.cpu_data_updated.connect(self.on_cpu_data_updated)
        self.add_grid_lines()
        self._load_current_profile()  # 프로필 로드

        if self._has_saved_layout():
            self.load_layout()  # 저장된 레이아웃이 있으면 복구
        else:
            self.create_tiles()  # 없으면 기본 생성
        self.update_minimum_size()
        self.customContextMenuRequested.connect(self.show_context_menu)

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
        # 프로필 메뉴 생성
        profile_menu = menu.addMenu("프로필")

        # ✅ 현재 프로필은 부모 탭에서 가져옴
        current_profile = self.parent_tab.current_profile

        # 체크 상태 업데이트
        action_all = profile_menu.addAction("Profile_ALL")
        action_all.setCheckable(True)
        action_all.setChecked(current_profile == "ALL")
        action_all.triggered.connect(lambda: self.parent_tab.set_profile("ALL"))

        action_graph = profile_menu.addAction("Profile_Graph")
        action_graph.setCheckable(True)
        action_graph.setChecked(current_profile == "GRAPH")
        action_graph.triggered.connect(lambda: self.parent_tab.set_profile("GRAPH"))

        action_gauge = profile_menu.addAction("Profile_Gauge")
        action_gauge.setCheckable(True)
        action_gauge.setChecked(current_profile == "GAUGE")
        action_gauge.triggered.connect(lambda: self.parent_tab.set_profile("GAUGE"))

        # 기존 메뉴 항목
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

    def _update_profile_checks(self):
        """현재 프로필에 따라 체크 상태 업데이트"""
        self.profile_all_action.setChecked(self.current_profile == "ALL")
        self.profile_graph_action.setChecked(self.current_profile == "GRAPH")
        self.profile_gauge_action.setChecked(self.current_profile == "GAUGE")

    def change_profile(self, profile_name: str):
        """프로필 변경 시 호출 (부모 탭의 신호를 통해 호출됨)"""
        self.current_profile = profile_name
        self.load_layout()

    def get_profile_filename(self):
        """프로필 기반 파일명"""
        return f"dashboard_state_{self.parent_tab.current_profile}.json"

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
                text=f"{core_id}",
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
                text=f"{core_id}",
                all_tiles=self.tiles,
                tile_model=graph_model,
            )
            graph_tile.setRect(0, 0, graph_model.width, graph_model.height)
            graph_tile.setPos(graph_model.x, graph_model.y)
            graph_tile.viewmodel = self.viewmodel
            self.scene.addItem(graph_tile)
            graph_tile.set_enabled(self.edit_mode)
            self.tiles.append(graph_tile)

            color_demo_model = TileModel(
                x=450,
                y=10,
                width=200,
                height=180,
                widget_type="ColorDemoWidget",
                core_id="demo",
            )
            self.model.add_tile(color_demo_model)
            color_demo_widget = ColorDemoWidget(
                color=QColor(255, 100, 100, 180)
            )  # 원하는 색상 지정
            color_demo_tile = ResizableTileItem(
                self.grid_size,
                cols=10,
                rows=10,
                widget=color_demo_widget,
                color=QColor(80, 80, 80, 180),
                text="Color Demo",
                all_tiles=self.tiles,
                tile_model=color_demo_model,
            )
            color_demo_tile.setRect(
                0, 0, color_demo_model.width, color_demo_model.height
            )
            color_demo_tile.setPos(color_demo_model.x, color_demo_model.y)
            color_demo_tile.viewmodel = self.viewmodel
            self.scene.addItem(color_demo_tile)
            color_demo_tile.set_enabled(self.edit_mode)
            self.tiles.append(color_demo_tile)

    def save_layout(self):
        filename = self.get_profile_filename()
        # 기존 파일 읽기
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        else:
            all_data = {}

        # 현재 시스템 데이터 갱신
        all_data[self.system_name] = self.model.to_dict()

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2)

    def load_layout(self):
        filename = self.get_profile_filename()
        try:
            # 파일이 존재하면 전체 데이터 로드
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
                # 현재 시스템에 해당하는 데이터만 추출
                data = all_data.get(self.system_name, None)
                if data:
                    # 모델 갱신
                    self.model = SystemResourceModel.from_dict(data)
                    self.viewmodel.model = self.model

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
                            text=f"{tile_model.core_id}",
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

                    self.update_grid_and_tiles()
                    print(f"{self.system_name} 레이아웃 복구 성공")
                    return  # 성공 시 종료

            # 파일이 없거나 해당 시스템 데이터가 없으면 기본 타일 생성
            print(f"{self.system_name} 레이아웃 데이터 없음, 기본 타일 생성")
            self.create_tiles()

        except Exception as e:
            print(f"{self.system_name} 레이아웃 복구 실패: {e}")
            self.create_tiles()

    def _has_saved_layout(self):
        filename = self.get_profile_filename()
        return os.path.exists(filename) and os.path.getsize(filename) > 0

    def _save_current_profile(self):
        """현재 프로필을 설정 파일에 저장"""
        config = {"last_profile": self.current_profile, "system_name": self.system_name}
        with open("app_config.json", "w") as f:
            json.dump(config, f)

    def _load_current_profile(self):
        """저장된 프로필 불러오기"""
        try:
            with open("app_config.json", "r") as f:
                config = json.load(f)
                if config["system_name"] == self.system_name:
                    self.current_profile = config.get("last_profile", "ALL")
        except:
            self.current_profile = "ALL"

    def update_minimum_size(self):
        if not self.tiles:
            return
        max_right = max(tile.pos().x() + tile.rect().width() for tile in self.tiles)
        max_bottom = max(tile.pos().y() + tile.rect().height() for tile in self.tiles)
        margin = 10
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
