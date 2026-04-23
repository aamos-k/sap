from __future__ import annotations
from dataclasses import dataclass, field
from .limb import Limb, LimbId

TILE_SIZE = 16


@dataclass
class Character:
    body_x: float
    body_y: float
    limbs: dict[LimbId, Limb] = field(default_factory=dict)
    vel_y: float = 0.0
    max_hp: int = 10
    hp: int = 10
    is_player: bool = False
    alive: bool = True

    @classmethod
    def spawn_at(cls, wx: float, wy: float, is_player: bool = False) -> Character:
        limb_length = 52.0
        limbs = {
            LimbId.LEFT_ARM:  Limb(LimbId.LEFT_ARM,  wx - 20, wy - 10, anchored=False, length=limb_length),
            LimbId.RIGHT_ARM: Limb(LimbId.RIGHT_ARM, wx + 20, wy - 10, anchored=False, length=limb_length),
            LimbId.LEFT_LEG:  Limb(LimbId.LEFT_LEG,  wx - 12, wy + 20, anchored=True,  length=limb_length),
            LimbId.RIGHT_LEG: Limb(LimbId.RIGHT_LEG, wx + 12, wy + 20, anchored=True,  length=limb_length),
        }
        return cls(body_x=wx, body_y=wy, limbs=limbs, is_player=is_player)

    def anchored_count(self) -> int:
        return sum(1 for l in self.limbs.values() if l.anchored)

    def compute_body_position(self) -> None:
        """Update body_x/y from the average of anchored limb tips.
        If no limbs anchored, body stays at current pos (gravity in physics)."""
        anchored = [l for l in self.limbs.values() if l.anchored]
        if anchored:
            self.body_x = sum(l.tip_x for l in anchored) / len(anchored)
            self.body_y = sum(l.tip_y for l in anchored) / len(anchored)
            self.vel_y = 0.0

    def get_limb(self, lid: LimbId) -> Limb:
        return self.limbs[lid]

    def take_damage(self, amount: int = 1) -> None:
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False
