from __future__ import annotations
import pygame
from cave.grid import CaveGrid
from cave.marching_squares import build_segments
from rendering.camera import Camera

ROCK_COLOUR = (28, 22, 18)
AIR_COLOUR  = (12, 10, 14)
WALL_COLOUR = (90, 75, 65)
WALL_WIDTH  = 2


class CaveRenderer:
    def __init__(self, grid: CaveGrid) -> None:
        self._grid = grid
        self._surface: pygame.Surface | None = None
        self._rendered_height = 0   # grid height when surface was last built

    def rebuild(self) -> None:
        """Force a full surface rebuild on the next draw call."""
        self._surface = None
        self._rendered_height = 0

    def _build_static_surface(self) -> None:
        ts = self._grid.TILE_SIZE
        w  = self._grid.width  * ts
        h  = self._grid.height * ts

        surf = pygame.Surface((w, h))
        surf.fill(ROCK_COLOUR)

        tiles = self._grid.tiles
        for ty in range(self._grid.height):
            for tx in range(self._grid.width):
                if tiles[ty, tx] == 1:
                    surf.fill(AIR_COLOUR, pygame.Rect(tx * ts, ty * ts, ts, ts))

        for (x1, y1), (x2, y2) in build_segments(self._grid):
            pygame.draw.line(surf, WALL_COLOUR,
                             (int(x1), int(y1)), (int(x2), int(y2)),
                             WALL_WIDTH)

        self._surface = surf
        self._rendered_height = self._grid.height

    def _extend_surface(self) -> None:
        """Append new rows to the existing surface without a full rebuild."""
        old_surf = self._surface
        ts       = self._grid.TILE_SIZE
        w        = self._grid.width  * ts
        old_h_px = self._rendered_height * ts
        new_h_px = self._grid.height    * ts

        new_surf = pygame.Surface((w, new_h_px))
        new_surf.fill(ROCK_COLOUR)
        new_surf.blit(old_surf, (0, 0))

        # Fill new tile rows
        tiles     = self._grid.tiles
        row_start = self._rendered_height
        for ty in range(row_start, self._grid.height):
            for tx in range(self._grid.width):
                if tiles[ty, tx] == 1:
                    new_surf.fill(AIR_COLOUR,
                                  pygame.Rect(tx * ts, ty * ts, ts, ts))

        # Draw marching-squares wall edges for the new (+ one overlap) rows
        seam = max(0, row_start - 1)
        for (x1, y1), (x2, y2) in build_segments(self._grid,
                                                   row_start=seam,
                                                   row_end=self._grid.height):
            pygame.draw.line(new_surf, WALL_COLOUR,
                             (int(x1), int(y1)), (int(x2), int(y2)),
                             WALL_WIDTH)

        self._surface = new_surf
        self._rendered_height = self._grid.height

    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        if self._surface is None:
            self._build_static_surface()
        elif self._grid.height != self._rendered_height:
            self._extend_surface()

        surf = self._surface
        sw, sh = screen.get_size()

        wx0 = camera.x
        wy0 = camera.y
        wx1 = wx0 + sw / camera.zoom
        wy1 = wy0 + sh / camera.zoom

        src_x = max(0, int(wx0))
        src_y = max(0, int(wy0))
        src_w = min(surf.get_width()  - src_x, int(wx1 - src_x) + 1)
        src_h = min(surf.get_height() - src_y, int(wy1 - src_y) + 1)

        if src_w <= 0 or src_h <= 0:
            return

        src_rect = pygame.Rect(src_x, src_y, src_w, src_h)
        chunk = surf.subsurface(src_rect)

        if camera.zoom != 1.0:
            chunk = pygame.transform.scale(
                chunk, (int(src_w * camera.zoom), int(src_h * camera.zoom)))

        dst_x, dst_y = camera.world_to_screen(src_x, src_y)
        screen.blit(chunk, (dst_x, dst_y))
