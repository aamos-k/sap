from __future__ import annotations
import math
import random
from collections import deque
from .grid import CaveGrid

_DOWN = math.pi / 2  # screen-space downward direction


def generate_cave(width: int = 400, height: int = 200,
                  seed: int = 0) -> tuple[CaveGrid, tuple[int, int], list[tuple[int, int]]]:
    """
    Returns (grid, bulb_centre_tile, room_centres_tiles).
    Starting room is near the top-centre; tunnels grow mostly downward.
    """
    rng = random.Random(seed)
    grid = CaveGrid.empty(width, height)

    # Starting room near the top-centre of the map
    bulb_cx = width // 2
    bulb_cy = 8

    grid.carve_ellipse(bulb_cx, bulb_cy, rx=8, ry=6, noise_amplitude=2.0, rng=rng)

    room_centres: list[tuple[int, int]] = []

    _carve_arm(grid, rng, bulb_cx, bulb_cy,
               angle=_DOWN, depth=0, max_depth=5,
               room_centres=room_centres)

    _flood_fill_prune(grid, bulb_cx, bulb_cy)

    _seal_border(grid)

    return grid, (bulb_cx, bulb_cy), room_centres


def generate_extension(grid: CaveGrid, rng: random.Random,
                       room_centres: list[tuple[int, int]],
                       extension_height: int = 150) -> None:
    """
    Carve new cave content into the bottom extension_height rows of grid.
    Call *after* grid.extend_down(extension_height).  Connects arms from open
    tiles near the seam and prunes orphan tiles.
    """
    seam_y = grid.height - extension_height - 4
    seam_y = max(2, seam_y)

    # Find open tiles near the seam to use as arm anchors
    open_xs = [tx for tx in range(3, grid.width - 3)
               if grid.is_open(tx, seam_y)]

    if not open_xs:
        open_xs = [grid.width // 2]

    # Pick up to 3 evenly-spaced start points for variety
    step = max(1, len(open_xs) // 3)
    starts = open_xs[::step][:3]

    for sx in starts:
        _carve_arm(grid, rng, sx, seam_y,
                   angle=_DOWN + rng.uniform(-0.35, 0.35),
                   depth=1, max_depth=4,
                   room_centres=room_centres)

    # Prune unreachable tiles using the first open cell in the top rows
    seed_tx, seed_ty = _find_first_open(grid)
    if seed_tx is not None:
        _flood_fill_prune(grid, seed_tx, seed_ty)

    _seal_border(grid)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _carve_arm(grid: CaveGrid, rng: random.Random,
               start_x: int, start_y: int,
               angle: float, depth: int, max_depth: int,
               room_centres: list) -> None:
    if depth > max_depth:
        return
    if rng.random() < 0.10 * depth:
        return

    tunnel_width = rng.randint(1, 2)
    tunnel_length = rng.randint(50, 110)
    approach_steps = rng.randint(4, 8)
    room_rx = rng.randint(4, 8)
    room_ry = rng.randint(3, 6)

    cx, cy = float(start_x), float(start_y)

    for _ in range(tunnel_length):
        # Gently pull angle back toward straight-down to keep caves downward-biased
        angle_err = angle - _DOWN
        angle -= angle_err * 0.08
        angle += rng.uniform(-0.22, 0.22)
        cx += math.cos(angle)
        cy += math.sin(angle)
        cx = max(4.0, min(grid.width - 5.0, cx))
        cy = max(4.0, min(grid.height - 5.0, cy))
        grid.carve_circle(int(cx), int(cy), radius=tunnel_width)

    for i in range(approach_steps):
        t = i / approach_steps
        w = tunnel_width + t * (room_ry * 0.35)
        angle += rng.uniform(-0.12, 0.12)
        cx += math.cos(angle)
        cy += math.sin(angle)
        cx = max(4.0, min(grid.width - 5.0, cx))
        cy = max(4.0, min(grid.height - 5.0, cy))
        grid.carve_circle(int(cx), int(cy), radius=max(1, int(w)))

    room_cx, room_cy = int(cx), int(cy)
    grid.carve_ellipse(room_cx, room_cy, rx=room_rx, ry=room_ry,
                       noise_amplitude=2.0, rng=rng)
    room_centres.append((room_cx, room_cy))

    num_branches = rng.randint(2, 4)
    for _ in range(num_branches):
        # Branches can spread sideways more at greater depth, but still bias down
        spread = math.pi * (0.30 + 0.08 * depth)
        new_angle = angle + rng.uniform(-spread, spread)
        _carve_arm(grid, rng, room_cx, room_cy,
                   new_angle, depth + 1, max_depth, room_centres)


def _flood_fill_prune(grid: CaveGrid, seed_tx: int, seed_ty: int) -> None:
    """Remove open tiles not reachable from the seed position."""
    import numpy as np
    reachable = np.zeros((grid.height, grid.width), dtype=bool)

    queue = deque()
    if grid.is_open(seed_tx, seed_ty):
        queue.append((seed_tx, seed_ty))
        reachable[seed_ty, seed_tx] = True

    while queue:
        tx, ty = queue.popleft()
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = tx + dx, ty + dy
            if grid.in_bounds(nx, ny) and not reachable[ny, nx] and grid.is_open(nx, ny):
                reachable[ny, nx] = True
                queue.append((nx, ny))

    grid.tiles[~reachable] = 0


def _seal_border(grid: CaveGrid) -> None:
    """Enforce a solid 2-tile border around the entire grid."""
    grid.tiles[:2, :] = 0
    grid.tiles[-2:, :] = 0
    grid.tiles[:, :2] = 0
    grid.tiles[:, -2:] = 0


def _find_first_open(grid: CaveGrid) -> tuple[int | None, int | None]:
    for ty in range(2, grid.height):
        for tx in range(2, grid.width - 2):
            if grid.is_open(tx, ty):
                return tx, ty
    return None, None
