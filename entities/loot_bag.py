from __future__ import annotations
import math
import random
from dataclasses import dataclass
from cave.grid import CaveGrid

GRAVITY = 600.0      # px / s²
BOUNCE_Y = 0.40      # coefficient of restitution (vertical)
FRICTION = 0.65      # horizontal speed multiplier each floor bounce
BAG_RADIUS = 8       # px — bag collision radius
COIN_RADIUS = 4      # px — coin collision radius
SPILL_DIST = 22.0    # px — limb-tip distance that triggers spill
COIN_COUNT = 8       # coins ejected when bag spills
SETTLE_SPEED = 10.0  # px/s — vertical speed below which object settles


@dataclass
class Coin:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    settled: bool = False


class LootBag:
    def __init__(self, x: float, y: float, rng: random.Random | None = None):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.spilled = False
        self.settled = False
        self.coins: list[Coin] = []
        self._rng = rng or random.Random()

    # ── Per-frame physics update ──────────────────────────────────────────

    def update(self, grid: CaveGrid, dt: float) -> None:
        if self.spilled:
            for coin in self.coins:
                if not coin.settled:
                    _step_coin(coin, grid, dt)
        elif not self.settled:
            _step_bag(self, grid, dt)

    # ── Spill trigger ─────────────────────────────────────────────────────

    def check_spill(self, limb_tips: list[tuple[float, float]]) -> None:
        if self.spilled:
            return
        for tx, ty in limb_tips:
            if math.hypot(tx - self.x, ty - self.y) < SPILL_DIST:
                self._do_spill()
                return

    def _do_spill(self) -> None:
        self.spilled = True
        rng = self._rng
        for _ in range(COIN_COUNT):
            angle = rng.uniform(0, 2 * math.pi)
            speed = rng.uniform(80, 260)
            self.coins.append(Coin(
                x=self.x,
                y=self.y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed - 120.0,  # bias upward on spill
            ))


# ── Physics helpers ────────────────────────────────────────────────────────────

def _step_bag(bag: LootBag, grid: CaveGrid, dt: float) -> None:
    bag.vy = min(bag.vy + GRAVITY * dt, 1200.0)

    nx = bag.x + bag.vx * dt
    ny = bag.y + bag.vy * dt

    ts = grid.TILE_SIZE

    # Vertical collision — bottom edge
    ttx, tty = grid.world_to_tile(nx, ny + BAG_RADIUS)
    if grid.is_solid(ttx, tty):
        ny = tty * ts - BAG_RADIUS
        bag.vy = -bag.vy * BOUNCE_Y
        bag.vx *= FRICTION
        if abs(bag.vy) < SETTLE_SPEED:
            bag.vy = 0.0
            ftx, fty = grid.world_to_tile(nx, ny + BAG_RADIUS + 2)
            if grid.is_solid(ftx, fty):
                bag.settled = True

    # Horizontal collision — leading edge
    side_x = nx + (BAG_RADIUS if bag.vx > 0 else -BAG_RADIUS)
    ttx2, tty2 = grid.world_to_tile(side_x, ny)
    if grid.is_solid(ttx2, tty2):
        nx = bag.x
        bag.vx = -bag.vx * 0.5

    bag.x = nx
    bag.y = ny


def _step_coin(coin: Coin, grid: CaveGrid, dt: float) -> None:
    coin.vy = min(coin.vy + GRAVITY * dt, 1200.0)

    nx = coin.x + coin.vx * dt
    ny = coin.y + coin.vy * dt

    ts = grid.TILE_SIZE

    # Vertical collision
    ttx, tty = grid.world_to_tile(nx, ny + COIN_RADIUS)
    if grid.is_solid(ttx, tty):
        ny = tty * ts - COIN_RADIUS
        coin.vy = -coin.vy * BOUNCE_Y
        coin.vx *= FRICTION
        if abs(coin.vy) < SETTLE_SPEED:
            coin.vy = 0.0
            ftx, fty = grid.world_to_tile(nx, ny + COIN_RADIUS + 2)
            if grid.is_solid(ftx, fty):
                coin.settled = True

    # Horizontal collision
    side_x = nx + (COIN_RADIUS if coin.vx > 0 else -COIN_RADIUS)
    ttx2, tty2 = grid.world_to_tile(side_x, ny)
    if grid.is_solid(ttx2, tty2):
        nx = coin.x
        coin.vx = -coin.vx * 0.55

    coin.x = nx
    coin.y = ny
