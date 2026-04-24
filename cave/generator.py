from __future__ import annotations
import math
import random
from collections import deque
from .grid import CaveGrid


def generate_cave(width: int = 400, height: int = 200,
                  seed: int = 0) -> tuple[CaveGrid, tuple[int, int], list[tuple[int, int]]]:
    """
    Returns (grid, bulb_centre_tile, room_centres_tiles).
    bulb_centre_tile is where the player spawns (in tile coords).
    room_centres_tiles[0] is where the first enemy spawns.
    """
    rng = random.Random(seed)
    grid = CaveGrid.empty(width, height)

    bulb_cx = width // 5
    bulb_cy = height // 2

    # Phase 1: bulb cavern (smaller so arms feel more earned)
    grid.carve_ellipse(bulb_cx, bulb_cy, rx=8, ry=6, noise_amplitude=2.0, rng=rng)

    room_centres: list[tuple[int, int]] = []

    # Phase 2: recursive arms
    _carve_arm(grid, rng, bulb_cx, bulb_cy,
               angle=0.0, depth=0, max_depth=5,
               room_centres=room_centres)

    # Phase 3: flood-fill connectivity from bulb
    _flood_fill_prune(grid, bulb_cx, bulb_cy)

    # Phase 4: enforce solid border (2-tile border)
    grid.tiles[:2, :] = 0
    grid.tiles[-2:, :] = 0
    grid.tiles[:, :2] = 0
    grid.tiles[:, -2:] = 0

    return grid, (bulb_cx, bulb_cy), room_centres


def _carve_arm(grid: CaveGrid, rng: random.Random,
               start_x: int, start_y: int,
               angle: float, depth: int, max_depth: int,
               room_centres: list) -> None:
    if depth > max_depth:
        return
    exit_prob = 0.1 * depth
    if rng.random() < exit_prob:
        return

    tunnel_width = rng.randint(1, 2)           # narrower (was 1–3)
    tunnel_length = rng.randint(50, 110)       # longer   (was 20–50)
    approach_steps = rng.randint(4, 8)         # shorter flare (was 8–16)
    room_rx = rng.randint(4, 8)               # smaller rooms (was 6–13)
    room_ry = rng.randint(3, 6)               # smaller rooms (was 5–10)

    cx, cy = float(start_x), float(start_y)

    # Thin tunnel — more winding angle for spindliness
    for _ in range(tunnel_length):
        angle += rng.uniform(-0.25, 0.25)
        cx += math.cos(angle)
        cy += math.sin(angle)
        cx = max(4.0, min(grid.width - 5.0, cx))
        cy = max(4.0, min(grid.height - 5.0, cy))
        grid.carve_circle(int(cx), int(cy), radius=tunnel_width)

    # Widening approach — gentler flare so rooms stay tight
    for i in range(approach_steps):
        t = i / approach_steps
        w = tunnel_width + t * (room_ry * 0.35)
        angle += rng.uniform(-0.12, 0.12)
        cx += math.cos(angle)
        cy += math.sin(angle)
        cx = max(4.0, min(grid.width - 5.0, cx))
        cy = max(4.0, min(grid.height - 5.0, cy))
        grid.carve_circle(int(cx), int(cy), radius=max(1, int(w)))

    # Room
    room_cx, room_cy = int(cx), int(cy)
    grid.carve_ellipse(room_cx, room_cy, rx=room_rx, ry=room_ry,
                       noise_amplitude=2.0, rng=rng)
    room_centres.append((room_cx, room_cy))

    # Branch — more arms for better map coverage
    num_branches = rng.randint(2, 4)
    for _ in range(num_branches):
        new_angle = angle + rng.uniform(-math.pi / 2, math.pi / 2)
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

    # Seal unreachable open tiles
    grid.tiles[~reachable] = 0
