from __future__ import annotations
import numpy as np
from .grid import CaveGrid

# Edge indices
TOP, RIGHT, BOTTOM, LEFT = 0, 1, 2, 3

# For each 4-bit case, a list of (edge_a, edge_b) pairs forming line segments.
# Corners: bit3=TL, bit2=TR, bit1=BR, bit0=BL  (1=air, 0=rock)
EDGE_TABLE: dict[int, list[tuple[int, int]]] = {
    0:  [],
    1:  [(LEFT, BOTTOM)],
    2:  [(BOTTOM, RIGHT)],
    3:  [(LEFT, RIGHT)],
    4:  [(RIGHT, TOP)],
    5:  [(TOP, LEFT), (RIGHT, BOTTOM)],
    6:  [(TOP, BOTTOM)],
    7:  [(TOP, LEFT)],
    8:  [(TOP, LEFT)],
    9:  [(TOP, BOTTOM)],
    10: [(LEFT, TOP), (BOTTOM, RIGHT)],
    11: [(RIGHT, TOP)],
    12: [(LEFT, RIGHT)],
    13: [(BOTTOM, RIGHT)],
    14: [(LEFT, BOTTOM)],
    15: [],
}


def build_segments(grid: CaveGrid,
                   row_start: int = 0,
                   row_end: int | None = None,
                   ) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """
    Return ((x1,y1),(x2,y2)) pixel-space segments for cave wall edges.

    row_start / row_end optionally restrict processing to a tile-row range
    (both exclusive of the upper bound, same semantics as range()).
    """
    ts = grid.TILE_SIZE
    tiles = grid.tiles
    h, w = tiles.shape

    if row_end is None:
        row_end = h - 1
    else:
        row_end = min(row_end, h - 1)
    row_start = max(0, row_start)

    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []

    for ty in range(row_start, row_end):
        for tx in range(w - 1):
            tl = int(tiles[ty,     tx    ])
            tr = int(tiles[ty,     tx + 1])
            br = int(tiles[ty + 1, tx + 1])
            bl = int(tiles[ty + 1, tx    ])

            case = (tl << 3) | (tr << 2) | (br << 1) | bl

            if case == 0 or case == 15:
                continue

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
