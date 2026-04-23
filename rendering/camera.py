from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Camera:
    x: float          # world-pixel x of viewport top-left
    y: float
    screen_w: int
    screen_h: int
    zoom: float = 1.0

    def world_to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        sx = (wx - self.x) * self.zoom
        sy = (wy - self.y) * self.zoom
        return int(sx), int(sy)

    def screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        wx = sx / self.zoom + self.x
        wy = sy / self.zoom + self.y
        return wx, wy

    def follow(self, target_x: float, target_y: float, lerp: float = 0.08) -> None:
        desired_x = target_x - self.screen_w / (2 * self.zoom)
        desired_y = target_y - self.screen_h / (2 * self.zoom)
        self.x += (desired_x - self.x) * lerp
        self.y += (desired_y - self.y) * lerp
