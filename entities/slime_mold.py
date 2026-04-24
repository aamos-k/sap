from __future__ import annotations
import math
import random
from .enemy import Enemy
from .character import Character
from .limb import LimbId
from cave.grid import CaveGrid

NUM_CANDIDATES = 24


class SlimeMold(Enemy):
    """Wall-clinging slime mold enemy. Lower HP, can anchor to any surface."""

    @classmethod
    def create(cls, wx: float, wy: float) -> SlimeMold:
        c = Character.spawn_at(wx, wy, is_player=False)
        c.max_hp = 6
        c.hp = 6
        s = cls.__new__(cls)
        s.__dict__.update(c.__dict__)
        s.sprite_prefix = 'slime'
        return s

    def choose_move(self, grid: CaveGrid, player_x: float, player_y: float,
                    rng: random.Random) -> tuple[LimbId, float, float]:
        best_score = -math.inf
        best_move: tuple[LimbId, float, float] = (LimbId.LEFT_LEG, self.body_x, self.body_y + 16)

        for limb_id, limb in self.limbs.items():
            for _ in range(NUM_CANDIDATES):
                angle = rng.uniform(0, 2 * math.pi)
                dist = rng.uniform(limb.length * 0.25, limb.length)
                tx = self.body_x + math.cos(angle) * dist
                ty = self.body_y + math.sin(angle) * dist

                score = _slime_score(limb_id, tx, ty, self, grid, player_x, player_y)
                if score > best_score:
                    best_score = score
                    best_move = (limb_id, tx, ty)

        return best_move


def _slime_would_anchor(tx: float, ty: float, grid: CaveGrid) -> bool:
    """Slime anchors to any adjacent solid — wall, floor, or ceiling."""
    ttx, tty = grid.world_to_tile(tx, ty)
    if grid.is_solid(ttx, tty):
        return False
    for nx, ny in grid.neighbours8(ttx, tty):
        if grid.is_solid(nx, ny):
            return True
    return False


def _slime_score(limb_id: LimbId, tx: float, ty: float,
                 slime: SlimeMold, grid: CaveGrid,
                 player_x: float, player_y: float) -> float:
    score = 0.0

    if _slime_would_anchor(tx, ty, grid):
        score += 10.0
    else:
        score -= 5.0

    other_anchored = sum(
        1 for lid, l in slime.limbs.items()
        if lid != limb_id and l.anchored
    )
    score += other_anchored * 2.0

    # Slime is more aggressive — 5× stronger approach bias
    dist_to_player = math.hypot(tx - player_x, ty - player_y)
    score -= dist_to_player * 0.05

    ttx, tty = grid.world_to_tile(tx, ty)
    if grid.is_solid(ttx, tty):
        score -= 20.0

    return score
