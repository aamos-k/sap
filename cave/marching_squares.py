from __future__ import annotations
import numpy as np
from .grid import CaveGrid

# Edge indices
TOP, RIGHT, BOTTOM, LEFT = 0, 1, 2, 3

# For each 4-bit case, a list of (edge_a, edge_b) pairs forming line segments.
# Corners: bit3=TL, bit2=TR, bit1=BR, bit0=BL  (1=air, 0=rock)
# Segments cross between air and rock regions.
EDGE_TABLE: dict[int, list[tuple[int, int]]] = {
    0:  [],
    1:  [(LEFT, BOTTOM)],
    2:  [(BOTTOM, RIGHT)],
    3:  [(LEFT, RIGHT)],
    4:  [(RIGHT, TOP)],
    5:  [(TOP, LEFT), (RIGHT, BOTTOM)],   # ambiguous: outer split
    6:  [(TOP, BOTTOM)],
    7:  [(TOP, LEFT)],
    8:  [(TOP, LEFT)],
    9:  [(TOP, BOTTOM)],
    10: [(LEFT, TOP), (BOTTOM, RIGHT)],   # ambiguous: outer split
    11: [(RIGHT, TOP)],
    12: [(LEFT, RIGHT)],
    13: [(BOTTOM, RIGHT)],
    14: [(LEFT, BOTTOM)],
    15: [],
}


def build_segments(grid: CaveGrid) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Return list of ((x1,y1),(x2,y2)) pixel-space line segments for cave walls."""
    ts = grid.TILE_SIZE
    tiles = grid.tiles
    h, w = tiles.shape
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []

    for ty in range(h - 1):
        for tx in range(w - 1):
            tl = int(tiles[ty,     tx    ])
            tr = int(tiles[ty,     tx + 1])
            br = int(tiles[ty + 1, tx + 1])
            bl = int(tiles[ty + 1, tx    ])

            case = (tl << 3) | (tr << 2) | (br << 1) | bl

            if case == 0 or case == 15:
                continue

            # Midpoint pixel coords of each edge of this cell
            mx = tx * ts
            my = ty * ts
            midpoints = {
                TOP:    (mx + ts / 2, my),
                RIGHT:  (mx + ts,     my + ts / 2),
                BOTTOM: (mx + ts / 2, my + ts),
                LEFT:   (mx,          my + ts / 2),
            }

            for ea, eb in EDGE_TABLE[case]:
                segments.append((midpoints[ea], midpoints[eb]))

    return segments
