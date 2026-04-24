from __future__ import annotations
import math
import random
from .character import Character
from .limb import LimbId
from cave.grid import CaveGrid

NUM_CANDIDATES = 24


class Enemy(Character):
    @classmethod
    def create(cls, wx: float, wy: float) -> Enemy:
        c = Character.spawn_at(wx, wy, is_player=False)
        e = cls.__new__(cls)
        e.__dict__.update(c.__dict__)
        return e

    def anchor_limb(self, limb, grid: CaveGrid) -> None:
        """Resolve anchoring after a limb move. Overridable per enemy type."""
        from game.physics import resolve_anchoring
        resolve_anchoring(limb, grid)

    def choose_move(self, grid: CaveGrid, player_x: float, player_y: float,
                    rng: random.Random) -> tuple[LimbId, float, float]:
        best_score = -math.inf
        best_move: tuple[LimbId, float, float] = (LimbId.LEFT_LEG, self.body_x, self.body_y + 16)

        player_dist = math.hypot(player_x - self.body_x, player_y - self.body_y)

        for limb_id, limb in self.limbs.items():
            for _ in range(NUM_CANDIDATES):
                angle = rng.uniform(0, 2 * math.pi)
                dist = rng.uniform(limb.length * 0.3, limb.length)
                tx = self.body_x + math.cos(angle) * dist
                ty = self.body_y + math.sin(angle) * dist

                score = _score_position(limb_id, tx, ty, self, grid, player_x, player_y)
                if score > best_score:
                    best_score = score
                    best_move = (limb_id, tx, ty)

        return best_move


def _score_position(limb_id: LimbId, tx: float, ty: float,
                    enemy: Enemy, grid: CaveGrid,
                    player_x: float, player_y: float) -> float:
    from game.physics import would_anchor
    score = 0.0

    # Strongly prefer anchoring
    if would_anchor(limb_id, tx, ty, grid):
        score += 10.0
    else:
        score -= 5.0

    # Prefer keeping at least 2 limbs total anchored
    other_anchored = sum(
        1 for lid, l in enemy.limbs.items()
        if lid != limb_id and l.anchored
    )
    score += other_anchored * 2.0

    # Mild preference toward player
    dist_to_player = math.hypot(tx - player_x, ty - player_y)
    score -= dist_to_player * 0.01

    # Penalty for trying to go into solid rock
    ttx, tty = grid.world_to_tile(tx, ty)
    if grid.is_solid(ttx, tty):
        score -= 20.0

    return score
