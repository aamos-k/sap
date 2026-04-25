from __future__ import annotations
import math
import random
from .character import Character
from .limb import LimbId
from cave.grid import CaveGrid
from game.ga import DEFAULT_GENES

NUM_CANDIDATES = 24


class Enemy(Character):
    # Extra fields set in create() — not dataclass fields
    genes: dict[str, float]
    damage_dealt: int

    @classmethod
    def create(cls, wx: float, wy: float,
               genes: dict[str, float] | None = None) -> Enemy:
        c = Character.spawn_at(wx, wy, is_player=False)
        e = cls.__new__(cls)
        e.__dict__.update(c.__dict__)
        e.genes = dict(DEFAULT_GENES) if genes is None else dict(genes)
        e.damage_dealt = 0
        return e

    def choose_move(self, grid: CaveGrid, player_x: float, player_y: float,
                    rng: random.Random) -> tuple[LimbId, float, float]:
        best_score = -math.inf
        best_move: tuple[LimbId, float, float] = (LimbId.LEFT_LEG, self.body_x, self.body_y + 16)

        n_candidates = max(8, int(self.genes['candidates']))
        reach_min    = float(self.genes['reach_min'])

        for limb_id, limb in self.limbs.items():
            for _ in range(n_candidates):
                angle = rng.uniform(0, 2 * math.pi)
                dist  = rng.uniform(limb.length * reach_min, limb.length)
                tx    = self.body_x + math.cos(angle) * dist
                ty    = self.body_y + math.sin(angle) * dist
                score = _score_position(limb_id, tx, ty, self, grid, player_x, player_y)
                if score > best_score:
                    best_score = score
                    best_move  = (limb_id, tx, ty)

        return best_move


def _score_position(limb_id: LimbId, tx: float, ty: float,
                    enemy: Enemy, grid: CaveGrid,
                    player_x: float, player_y: float) -> float:
    from game.physics import would_anchor
    genes = enemy.genes
    score = 0.0

    if would_anchor(limb_id, tx, ty, grid):
        score += genes['anchor_weight']
    else:
        score -= genes['float_penalty']

    other_anchored = sum(
        1 for lid, l in enemy.limbs.items()
        if lid != limb_id and l.anchored
    )
    score += other_anchored * genes['stability_weight']

    dist_to_player = math.hypot(tx - player_x, ty - player_y)
    score -= dist_to_player * genes['aggression']

    ttx, tty = grid.world_to_tile(tx, ty)
    if grid.is_solid(ttx, tty):
        score -= 20.0

    return score
