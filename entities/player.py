from __future__ import annotations
from .character import Character


class Player(Character):
    @classmethod
    def create(cls, wx: float, wy: float) -> Player:
        c = Character.spawn_at(wx, wy, is_player=True)
        p = cls.__new__(cls)
        p.__dict__.update(c.__dict__)
        return p
