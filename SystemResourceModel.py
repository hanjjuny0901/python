from typing import List, Dict


class TileModel:
    """개별 타일의 상태 관리"""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        widget_type: str,
        core_id: str,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.widget_type = widget_type  # "CircularGauge" 또는 "CPUGraphWidget"
        self.core_id = core_id  # "core1", "core2" 등


class SystemResourceModel:
    """전체 시스템 리소스 데이터 중앙 관리"""

    def __init__(self):
        self.cpu_cores: Dict[str, float] = {}  # { "core1": 75.0, "core2": 60.0 }
        self.tiles: List[TileModel] = []  # 모든 타일 정보

    def update_cpu_data(self, new_data: Dict[str, float]):
        """CPU 코어 데이터 일괄 업데이트"""
        self.cpu_cores = new_data

    def add_tile(self, tile: TileModel):
        """새 타일 추가"""
        self.tiles.append(tile)

    def to_dict(self) -> dict:
        """JSON 직렬화용 딕셔너리 변환"""
        return {
            "cpu_cores": self.cpu_cores,
            "tiles": [
                {
                    "x": tile.x,
                    "y": tile.y,
                    "width": tile.width,
                    "height": tile.height,
                    "widget_type": tile.widget_type,
                    "core_id": tile.core_id,
                }
                for tile in self.tiles
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SystemResourceModel":
        model = cls()
        model.cpu_cores = data.get("cpu_cores", {})
        model.tiles = [
            TileModel(
                x=float(t["x"]),  # 위치는 float 허용
                y=float(t["y"]),
                width=int(t["width"]),  # ✅ width/height는 int로 변환
                height=int(t["height"]),  # ✅
                widget_type=t["widget_type"],
                core_id=t["core_id"],
            )
            for t in data.get("tiles", [])
        ]
        return model
