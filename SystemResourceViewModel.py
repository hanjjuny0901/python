from PyQt5.QtCore import QObject, pyqtSignal
from SystemResourceModel import SystemResourceModel


class SystemResourceViewModel(QObject):
    cpu_data_updated = pyqtSignal(dict)  # { "core1": 값, ... }
    tiles_updated = pyqtSignal(list)  # 타일 정보 변경 시

    def __init__(self, model: SystemResourceModel):
        super().__init__()
        self._model = model

    # CPU 데이터 관련 메서드
    def update_cpu_values(self, new_values: dict):
        """CPU 데이터 업데이트 및 신호 발생"""
        self._model.update_cpu_data(new_values)
        self.cpu_data_updated.emit(new_values)

    def get_cpu_value(self, core_id: str) -> float:
        """특정 코어 값 조회"""
        return self._model.cpu_cores.get(core_id, 0.0)

    # 타일 관련 메서드
    def get_tile_state(self, index: int) -> dict:
        """타일 상태 반환"""
        tile = self._model.tiles[index]
        return {
            "x": tile.x,
            "y": tile.y,
            "width": tile.width,
            "height": tile.height,
            "widget_type": tile.widget_type,
            "core_id": tile.core_id,
        }

    def set_tile_state(self, index: int, state: dict):
        """타일 상태 업데이트"""
        tile = self._model.tiles[index]
        tile.x = state["x"]
        tile.y = state["y"]
        tile.width = state["width"]
        tile.height = state["height"]
        self.tiles_updated.emit(self._model.tiles)
