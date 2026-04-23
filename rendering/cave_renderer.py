from __future__ import annotations
import pygame
from cave.grid import CaveGrid
from cave.marching_squares import build_segments
from rendering.camera import Camera

ROCK_COLOUR  = (28, 22, 18)
AIR_COLOUR   = (12, 10, 14)
WALL_COLOUR  = (90, 75, 65)
WALL_WIDTH   = 2


class CaveRenderer:
    def __init__(self, grid: CaveGrid) -> None:
        self._grid = grid
        self._segments = build_segments(grid)
        self._surface: pygame.Surface | None = None
        self._surface_offset = (0, 0)

    def rebuild(self) -> None:
        self._segments = build_segments(self._grid)
        self._surface = None

    def _build_static_surface(self) -> None:
        """Pre-render the cave onto a large surface at world scale."""
        ts = self._grid.TILE_SIZE
        w = self._grid.width * ts
        h = self._grid.height * ts
        surf = pygame.Surface((w, h))
        surf.fill(ROCK_COLOUR)

        # Draw air tiles
        tiles = self._grid.tiles
        for ty in range(self._grid.height):
            for tx in range(self._grid.width):
                if tiles[ty, tx] == 1:
                    rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
                    surf.fill(AIR_COLOUR, rect)

        # Draw marching-squares wall edges
        for (x1, y1), (x2, y2) in self._segments:
            pygame.draw.line(surf, WALL_COLOUR,
                             (int(x1), int(y1)), (int(x2), int(y2)),
                             WALL_WIDTH)

        self._surface = surf

    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        if self._surface is None:
            self._build_static_surface()

        surf = self._surface
        sw, sh = screen.get_size()

        # World region visible on screen
        wx0 = camera.x
        wy0 = camera.y
        wx1 = wx0 + sw / camera.zoom
        wy1 = wy0 + sh / camera.zoom

        src_x = max(0, int(wx0))
        src_y = max(0, int(wy0))
        src_w = min(surf.get_width() - src_x,  int(wx1 - src_x) + 1)
        src_h = min(surf.get_height() - src_y, int(wy1 - src_y) + 1)

        if src_w <= 0 or src_h <= 0:
            return

        src_rect = pygame.Rect(src_x, src_y, src_w, src_h)
        chunk = surf.subsurface(src_rect)

        if camera.zoom != 1.0:
            dst_w = int(src_w * camera.zoom)
            dst_h = int(src_h * camera.zoom)
            chunk = pygame.transform.scale(chunk, (dst_w, dst_h))

        dst_x, dst_y = camera.world_to_screen(src_x, src_y)
        screen.blit(chunk, (dst_x, dst_y))
