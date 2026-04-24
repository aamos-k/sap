from __future__ import annotations
import random
from cave.generator import generate_cave
from cave.grid import CaveGrid
from entities.player import Player
from entities.enemy import Enemy
from entities.limb import LimbId
from game.physics import (resolve_anchoring, apply_gravity,
                           clamp_limb_to_open, check_collision_damage)
from game.turn_manager import TurnManager, TurnState
from rendering.camera import Camera

ENEMY_THINK_TICKS = 18   # ~0.3s at 60fps
TILE_SIZE = 16


class World:
    def __init__(self, seed: int = 0):
        self._rng = random.Random(seed + 99)

        grid, bulb, room_centres = generate_cave(width=400, height=200, seed=seed)
        self.grid: CaveGrid = grid

        bx, by = grid.tile_to_world(*bulb)
        self.player = Player.create(bx, by - TILE_SIZE)

        # Snap player legs to floor
        for lid in (LimbId.LEFT_LEG, LimbId.RIGHT_LEG):
            limb = self.player.get_limb(lid)
            clamp_limb_to_open(limb, grid)
            resolve_anchoring(limb, grid)
        self.player.compute_body_position()

        self.enemies: list[Enemy] = []
        if room_centres:
            ex, ey = grid.tile_to_world(*room_centres[0])
            enemy = Enemy.create(ex, ey - TILE_SIZE)
            for lid in (LimbId.LEFT_LEG, LimbId.RIGHT_LEG):
                limb = enemy.get_limb(lid)
                clamp_limb_to_open(limb, grid)
                resolve_anchoring(limb, grid)
            enemy.compute_body_position()
            self.enemies.append(enemy)

        self.turn_manager = TurnManager(player=self.player, enemies=self.enemies)
        self.camera = Camera(
            x=self.player.body_x - 640,
            y=self.player.body_y - 360,
            screen_w=1280,
            screen_h=720,
        )

        self._enemy_think_timer = 0

    @property
    def entities(self):
        yield self.player
        yield from self.enemies

    def tick(self) -> None:
        tm = self.turn_manager
        tm.tick_flash()

        if tm.state == TurnState.ENEMY_THINK:
            self._enemy_think_timer += 1
            if self._enemy_think_timer >= ENEMY_THINK_TICKS:
                self._enemy_think_timer = 0
                self._run_enemy_turns()

        self.camera.follow(self.player.body_x, self.player.body_y)

    def _run_enemy_turns(self) -> None:
        tm = self.turn_manager
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            lid, wx, wy = enemy.choose_move(
                self.grid, self.player.body_x, self.player.body_y, self._rng)
            limb = enemy.get_limb(lid)
            limb.tip_x, limb.tip_y = wx, wy
            clamp_limb_to_open(limb, self.grid)
            resolve_anchoring(limb, self.grid)
            enemy.compute_body_position()
            apply_gravity(enemy, self.grid)

            check_collision_damage(enemy, [self.player])
            if not self.player.alive:
                tm.set_game_over("enemy")
                return

        tm.advance_to_player()

    def apply_player_move(self, target_wx: float, target_wy: float) -> bool:
        """Move the selected player limb to target. Returns True on success."""
        tm = self.turn_manager
        if tm.selected_limb is None:
            return False

        limb = self.player.get_limb(tm.selected_limb)

        from game.physics import validate_limb_move
        if not validate_limb_move(self.player, limb, target_wx, target_wy):
            tm.set_flash("Too far!")
            return False

        limb.tip_x, limb.tip_y = target_wx, target_wy
        clamp_limb_to_open(limb, self.grid)
        resolve_anchoring(limb, self.grid)
        self.player.compute_body_position()
        apply_gravity(self.player, self.grid)

        check_collision_damage(self.player, self.enemies)
        # Check enemy deaths
        for enemy in self.enemies:
            if not enemy.alive:
                # All enemies dead?
                if all(not e.alive for e in self.enemies):
                    tm.set_game_over("player")
                    return True

        tm.advance_to_enemy()
        return True
