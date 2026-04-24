from __future__ import annotations
import math
import random
from .enemy import Enemy
from .character import Character
from .limb import LimbId
from cave.grid import CaveGrid

NUM_CANDIDATES = 24

# High viscosity: limbs move at most 40% of their reach per turn
_VISCOSITY_MAX = 0.40
_VISCOSITY_MIN = 0.05


class SlimeMold(Enemy):
    """Viscous liquid slime that pools on surfaces. Lower HP, flows downward."""

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
                # Viscous: short creeping steps only
                dist = rng.uniform(limb.length * _VISCOSITY_MIN, limb.length * _VISCOSITY_MAX)
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

    # Surface adhesion — liquid wets every surface it touches
    if _slime_would_anchor(tx, ty, grid):
        score += 10.0
    else:
        score -= 5.0

    # Stability: reward having other limbs still anchored
    other_anchored = sum(
        1 for lid, l in slime.limbs.items()
        if lid != limb_id and l.anchored
    )
    score += other_anchored * 2.0

    # Gravity: strongly prefer flowing downward (higher y = lower in world)
    score += (ty - slime.body_y) * 0.15

    # Cohesion: stay close to the blob centroid (high viscosity resists spreading)
    other_tips = [(l.tip_x, l.tip_y) for lid, l in slime.limbs.items() if lid != limb_id]
    if other_tips:
        cx = sum(x for x, _ in other_tips) / len(other_tips)
        cy = sum(y for _, y in other_tips) / len(other_tips)
        dist_to_centroid = math.hypot(tx - cx, ty - cy)
        score -= dist_to_centroid * 0.10

    # No solid tiles
    ttx, tty = grid.world_to_tile(tx, ty)
    if grid.is_solid(ttx, tty):
        score -= 20.0

    return score
