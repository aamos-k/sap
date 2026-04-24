from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto


class LimbId(Enum):
    LEFT_ARM  = auto()
    RIGHT_ARM = auto()
    LEFT_LEG  = auto()
    RIGHT_LEG = auto()


LIMB_LABELS = {
    LimbId.LEFT_ARM:  "LA",
    LimbId.RIGHT_ARM: "RA",
    LimbId.LEFT_LEG:  "LL",
    LimbId.RIGHT_LEG: "RL",
}

LIMB_KEYS = {
    LimbId.LEFT_ARM:  "1",
    LimbId.RIGHT_ARM: "2",
    LimbId.LEFT_LEG:  "3",
    LimbId.RIGHT_LEG: "4",
}


@dataclass
class Limb:
    id: LimbId
    tip_x: float
    tip_y: float
    anchored: bool = False
    length: float = 52.0  # pixels — ~3.25 tiles at 16px/tile
