from __future__ import annotations
import math
import random
from .enemy import Enemy
from .character import Character
from .limb import Limb, LimbId
from cave.grid import CaveGrid

# More candidates so the slime reliably finds a surface position each turn
NUM_CANDIDATES = 48

# Viscosity tuning — keep every limb glued to a surface at all times
_SURFACE_BOND  = 20.0   # bonus when the candidate spot touches any solid
_AIR_PENALTY   = 30.0   # penalty when the candidate spot floats free
_COHESION      = 8.0    # bonus per OTHER limb that is still anchored
_APPROACH_BIAS = 0.008  # per-pixel pull toward player (passive flow, not a chase)
_SOLID_PENALTY = 30.0   # penalty for candidate inside solid rock

# Movement range: 10–35 % of limb length → 5–18 px at default length of 52 px.
# This tiny step size is what makes the body "flow" rather than leap.
_STEP_MIN = 0.10
_STEP_MAX = 0.35


class SlimeMold(Enemy):
    """High-viscosity liquid enemy.  Creeps along every surface, never leaves contact."""

    @classmethod
    def create(cls, wx: float, wy: float) -> SlimeMold:
        c = Character.spawn_at(wx, wy, is_player=False)
        c.max_hp = 6
        c.hp = 6
        s = cls.__new__(cls)
        s.__dict__.update(c.__dict__)
        s.sprite_prefix = 'slime'
        return s

    # ── Any-surface anchoring ──────────────────────────────────────────────

    def anchor_limb(self, limb: Limb, grid: CaveGrid) -> None:
        """Slime sticks to any adjacent solid — wall, ceiling, or floor."""
        limb.anchored = _slime_would_anchor(limb.tip_x, limb.tip_y, grid)

    # ── Viscous-liquid movement ────────────────────────────────────────────

    def choose_move(self, grid: CaveGrid, player_x: float, player_y: float,
                    rng: random.Random) -> tuple[LimbId, float, float]:
        best_score = -math.inf
        best_move: tuple[LimbId, float, float] = (LimbId.LEFT_LEG, self.body_x, self.body_y + 16)

        for limb_id, limb in self.limbs.items():
            for _ in range(NUM_CANDIDATES):
                angle = rng.uniform(0, 2 * math.pi)
                dist  = rng.uniform(limb.length * _STEP_MIN, limb.length * _STEP_MAX)
                tx = self.body_x + math.cos(angle) * dist
                ty = self.body_y + math.sin(angle) * dist

                score = _score(limb_id, tx, ty, self, grid, player_x, player_y)
                if score > best_score:
                    best_score = score
                    best_move = (limb_id, tx, ty)

        return best_move


# ── Helpers ────────────────────────────────────────────────────────────────────

def _slime_would_anchor(tx: float, ty: float, grid: CaveGrid) -> bool:
    """True if the position touches any adjacent solid tile (wall, floor, ceiling)."""
    ttx, tty = grid.world_to_tile(tx, ty)
    if grid.is_solid(ttx, tty):
        return False
    for nx, ny in grid.neighbours8(ttx, tty):
        if grid.is_solid(nx, ny):
            return True
    return False


def _score(limb_id: LimbId, tx: float, ty: float,
           slime: SlimeMold, grid: CaveGrid,
           player_x: float, player_y: float) -> float:
    score = 0.0

    # Must stay on a surface — the dominant constraint
    if _slime_would_anchor(tx, ty, grid):
        score += _SURFACE_BOND
    else:
        score -= _AIR_PENALTY

    # Keep as many other limbs anchored as possible (blob cohesion)
    other_anchored = sum(
        1 for lid, l in slime.limbs.items()
        if lid != limb_id and l.anchored
    )
    score += other_anchored * _COHESION

    # Passive flow toward the player
    dist_to_player = math.hypot(tx - player_x, ty - player_y)
    score -= dist_to_player * _APPROACH_BIAS

    # Reject solid rock positions
    ttx, tty = grid.world_to_tile(tx, ty)
    if grid.is_solid(ttx, tty):
        score -= _SOLID_PENALTY

    return score
