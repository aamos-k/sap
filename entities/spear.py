from __future__ import annotations
import math
from dataclasses import dataclass, field
from cave.grid import CaveGrid

SPEAR_GRAVITY    = 380.0   # px/s² — lower than bags so it flies further
SPEAR_SPEED      = 680.0   # initial throw speed px/s
SPEAR_BOUNCE_Y   = 0.20    # low restitution — thuds into ground
SPEAR_FRICTION   = 0.35
SPEAR_RADIUS     = 5       # collision radius px
SPEAR_SETTLE_SPD = 20.0    # px/s — settle threshold
SPEAR_HIT_RADIUS = 18.0    # damage detection radius px
SPEAR_DAMAGE     = 2       # HP dealt per hit
RETRIEVE_DIST    = 22.0    # limb-tip distance that picks the spear back up


@dataclass
class Spear:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    in_flight: bool = False
    settled: bool = False
    held: bool = True
    _hit_ids: set = field(default_factory=set, repr=False)

    def throw(self, from_x: float, from_y: float,
              target_x: float, target_y: float) -> None:
        dx = target_x - from_x
        dy = target_y - from_y
        dist = math.hypot(dx, dy) or 1.0
        self.x = from_x
        self.y = from_y
        self.vx = (dx / dist) * SPEAR_SPEED
        self.vy = (dy / dist) * SPEAR_SPEED
        self.in_flight = True
        self.held = False
        self.settled = False
        self._hit_ids = set()

    def update(self, grid: CaveGrid, dt: float) -> None:
        if self.held or self.settled:
            return
        _step_spear(self, grid, dt)

    def check_retrieve(self, limb_tips: list[tuple[float, float]]) -> bool:
        """Returns True if a limb tip is close enough to retrieve the spear."""
        if self.held or self.in_flight:
            return False
        for tx, ty in limb_tips:
            if math.hypot(tx - self.x, ty - self.y) < RETRIEVE_DIST:
                self.held = True
                self.settled = False
                self._hit_ids = set()
                return True
        return False

    def check_hit(self, enemy) -> bool:
        """Returns True if the spear hits this enemy and has not hit it already."""
        if not self.in_flight:
            return False
        eid = id(enemy)
        if eid in self._hit_ids:
            return False
        if math.hypot(self.x - enemy.body_x, self.y - enemy.body_y) < SPEAR_HIT_RADIUS:
            self._hit_ids.add(eid)
            return True
        return False


def _step_spear(spear: Spear, grid: CaveGrid, dt: float) -> None:
    spear.vy = min(spear.vy + SPEAR_GRAVITY * dt, 1200.0)

    nx = spear.x + spear.vx * dt
    ny = spear.y + spear.vy * dt

    ts = grid.TILE_SIZE

    # Ceiling collision
    ttx, tty = grid.world_to_tile(nx, ny - SPEAR_RADIUS)
    if grid.is_solid(ttx, tty):
        ny = (tty + 1) * ts + SPEAR_RADIUS
        spear.vy = abs(spear.vy) * SPEAR_BOUNCE_Y

    # Floor collision
    ttx, tty = grid.world_to_tile(nx, ny + SPEAR_RADIUS)
    if grid.is_solid(ttx, tty):
        ny = tty * ts - SPEAR_RADIUS
        spear.vy = -spear.vy * SPEAR_BOUNCE_Y
        spear.vx *= SPEAR_FRICTION
        if abs(spear.vy) < SPEAR_SETTLE_SPD:
            spear.vy = 0.0
            spear.in_flight = False
            ftx, fty = grid.world_to_tile(nx, ny + SPEAR_RADIUS + 2)
            if grid.is_solid(ftx, fty):
                spear.settled = True

    # Horizontal (wall) collision
    side_x = nx + (SPEAR_RADIUS if spear.vx > 0 else -SPEAR_RADIUS)
    ttx2, tty2 = grid.world_to_tile(side_x, ny)
    if grid.is_solid(ttx2, tty2):
        nx = spear.x
        spear.vx = -spear.vx * 0.30

    spear.x = nx
    spear.y = ny
