from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar
import numpy as np


@dataclass
class CaveGrid:
    width: int
    height: int
    tiles: np.ndarray  # shape (height, width), uint8: 0=rock 1=air
    TILE_SIZE: ClassVar[int] = 16

    @classmethod
    def empty(cls, width: int, height: int) -> CaveGrid:
        return cls(width=width, height=height,
                   tiles=np.zeros((height, width), dtype=np.uint8))

    def in_bounds(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width and 0 <= ty < self.height

    def is_solid(self, tx: int, ty: int) -> bool:
        if not self.in_bounds(tx, ty):
            return True
        return self.tiles[ty, tx] == 0

    def is_open(self, tx: int, ty: int) -> bool:
        return not self.is_solid(tx, ty)

    def world_to_tile(self, wx: float, wy: float) -> tuple[int, int]:
        return int(wx // self.TILE_SIZE), int(wy // self.TILE_SIZE)

    def tile_to_world(self, tx: int, ty: int) -> tuple[float, float]:
        ts = self.TILE_SIZE
        return tx * ts + ts / 2, ty * ts + ts / 2

    def carve_circle(self, cx: int, cy: int, radius: int) -> None:
        r2 = radius * radius
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= r2:
                    tx, ty = cx + dx, cy + dy
                    if self.in_bounds(tx, ty):
                        self.tiles[ty, tx] = 1

    def carve_ellipse(self, cx: int, cy: int, rx: int, ry: int,
                      noise_amplitude: float = 0.0, rng=None) -> None:
        for dy in range(-ry - int(noise_amplitude) - 2, ry + int(noise_amplitude) + 3):
            for dx in range(-rx - int(noise_amplitude) - 2, rx + int(noise_amplitude) + 3):
                tx, ty = cx + dx, cy + dy
                if not self.in_bounds(tx, ty):
                    continue
                if noise_amplitude > 0 and rng is not None:
                    angle = 0.0 if (dx == 0 and dy == 0) else __import__('math').atan2(dy, dx)
                    n = _value_noise_2d(tx, ty) * noise_amplitude
                    nrx = max(1, rx + n)
                    nry = max(1, ry + n)
                else:
                    nrx, nry = float(rx), float(ry)
                if nrx > 0 and nry > 0:
                    if (dx / nrx) ** 2 + (dy / nry) ** 2 <= 1.0:
                        self.tiles[ty, tx] = 1

    def neighbours8(self, tx: int, ty: int):
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                yield tx + dx, ty + dy

    def snap_to_open(self, tx: int, ty: int) -> tuple[int, int] | None:
        """BFS to nearest open tile from (tx, ty)."""
        from collections import deque
        if self.is_open(tx, ty):
            return tx, ty
        visited = {(tx, ty)}
        queue = deque([(tx, ty)])
        while queue:
            cx, cy = queue.popleft()
            for nx, ny in self.neighbours8(cx, cy):
                if (nx, ny) not in visited and self.in_bounds(nx, ny):
                    visited.add((nx, ny))
                    if self.is_open(nx, ny):
                        return nx, ny
                    queue.append((nx, ny))
        return None


def _value_noise_2d(ix: int, iy: int, seed: int = 42) -> float:
    n = ix + iy * 57 + seed * 131
    n = (n << 13) ^ n
    val = 1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7FFFFFFF) / 1073741824.0
    return val
