from __future__ import annotations
import math
import random
from collections import deque
from .grid import CaveGrid


def generate_cave(width: int = 256, height: int = 128,
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

    # Phase 1: bulb cavern
    grid.carve_ellipse(bulb_cx, bulb_cy, rx=12, ry=9, noise_amplitude=3.0, rng=rng)

    room_centres: list[tuple[int, int]] = []

    # Phase 2: recursive arms
    _carve_arm(grid, rng, bulb_cx, bulb_cy,
               angle=0.0, depth=0, max_depth=4,
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

    tunnel_width = rng.randint(1, 3)
    tunnel_length = rng.randint(20, 50)
    approach_steps = rng.randint(8, 16)
    room_rx = rng.randint(6, 13)
    room_ry = rng.randint(5, 10)

    cx, cy = float(start_x), float(start_y)

    # Thin tunnel
    for _ in range(tunnel_length):
        angle += rng.uniform(-0.18, 0.18)
        cx += math.cos(angle)
        cy += math.sin(angle)
        # Clamp away from borders
        cx = max(4.0, min(grid.width - 5.0, cx))
        cy = max(4.0, min(grid.height - 5.0, cy))
        grid.carve_circle(int(cx), int(cy), radius=tunnel_width)

    # Widening approach
    for i in range(approach_steps):
        t = i / approach_steps
        w = tunnel_width + t * (room_ry * 0.6)
        angle += rng.uniform(-0.12, 0.12)
        cx += math.cos(angle)
        cy += math.sin(angle)
        cx = max(4.0, min(grid.width - 5.0, cx))
        cy = max(4.0, min(grid.height - 5.0, cy))
        grid.carve_circle(int(cx), int(cy), radius=max(1, int(w)))

    # Room
    room_cx, room_cy = int(cx), int(cy)
    grid.carve_ellipse(room_cx, room_cy, rx=room_rx, ry=room_ry,
                       noise_amplitude=2.5, rng=rng)
    room_centres.append((room_cx, room_cy))

    # Branch
    num_branches = rng.randint(1, 3)
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
