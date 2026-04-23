from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from entities.limb import LimbId
from entities.player import Player
from entities.enemy import Enemy


class TurnState(Enum):
    PLAYER_SELECT_LIMB   = auto()
    PLAYER_SELECT_TARGET = auto()
    PLAYER_RESOLVE       = auto()
    ENEMY_THINK          = auto()
    ENEMY_RESOLVE        = auto()
    GAME_OVER            = auto()


@dataclass
class TurnManager:
    player: Player
    enemies: list[Enemy]
    state: TurnState = TurnState.PLAYER_SELECT_LIMB
    selected_limb: LimbId | None = None
    turn_number: int = 0
    winner: str = ""          # "player" or "enemy"
    flash_message: str = ""   # transient feedback text
    _flash_timer: int = 0

    def select_limb(self, lid: LimbId) -> None:
        if self.state != TurnState.PLAYER_SELECT_LIMB:
            return
        self.selected_limb = lid
        self.state = TurnState.PLAYER_SELECT_TARGET

    def cancel_selection(self) -> None:
        self.selected_limb = None
        self.state = TurnState.PLAYER_SELECT_LIMB

    def commit_player_move(self) -> None:
        self.state = TurnState.PLAYER_RESOLVE

    def advance_to_enemy(self) -> None:
        self.state = TurnState.ENEMY_THINK

    def advance_to_player(self) -> None:
        self.turn_number += 1
        self.selected_limb = None
        self.state = TurnState.PLAYER_SELECT_LIMB

    def set_game_over(self, winner: str) -> None:
        self.winner = winner
        self.state = TurnState.GAME_OVER

    def set_flash(self, msg: str, ticks: int = 120) -> None:
        self.flash_message = msg
        self._flash_timer = ticks

    def tick_flash(self) -> None:
        if self._flash_timer > 0:
            self._flash_timer -= 1
            if self._flash_timer == 0:
                self.flash_message = ""
