from __future__ import annotations
import random
from cave.generator import generate_cave
from cave.grid import CaveGrid
from entities.player import Player
from entities.enemy import Enemy
from entities.slime_mold import SlimeMold
from entities.loot_bag import LootBag
from entities.limb import LimbId
from game.physics import (resolve_anchoring, apply_gravity,
                           clamp_limb_to_open, check_collision_damage)
from game.turn_manager import TurnManager, TurnState
from rendering.camera import Camera

ENEMY_THINK_TICKS = 18   # ~0.3s at 60fps
TILE_SIZE = 16
_DT = 1.0 / 60           # physics timestep (seconds per frame)


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

        # Spawn 1-2 enemies per room, skipping the first three rooms
        self.enemies: list[Enemy] = []
        for i, room_centre in enumerate(room_centres):
            if i < 3:
                continue
            ex, ey = grid.tile_to_world(*room_centre)
            count = self._rng.randint(1, 2)
            for j in range(count):
                offset_x = (j - (count - 1) / 2) * 26
                spawn_x = ex + offset_x
                spawn_y = ey - TILE_SIZE
                if self._rng.random() < 0.4:
                    enemy: Enemy = SlimeMold.create(spawn_x, spawn_y)
                else:
                    enemy = Enemy.create(spawn_x, spawn_y)
                for lid in (LimbId.LEFT_LEG, LimbId.RIGHT_LEG):
                    limb = enemy.get_limb(lid)
                    clamp_limb_to_open(limb, grid)
                    resolve_anchoring(limb, grid)
                enemy.compute_body_position()
                self.enemies.append(enemy)

        # One loot bag per room (all rooms)
        self.bags: list[LootBag] = []
        for room_centre in room_centres:
            bx_r, by_r = grid.tile_to_world(*room_centre)
            bag_rng = random.Random(self._rng.randint(0, 2 ** 32))
            bag = LootBag(bx_r, by_r - TILE_SIZE, rng=bag_rng)
            self.bags.append(bag)

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

        self._update_bags()
        self.camera.follow(self.player.body_x, self.player.body_y)

    def _player_limb_tips(self) -> list[tuple[float, float]]:
        return [(limb.tip_x, limb.tip_y) for limb in self.player.limbs.values()]

    def _update_bags(self) -> None:
        tips = self._player_limb_tips()
        for bag in self.bags:
            bag.check_spill(tips)
            bag.update(self.grid, _DT)

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
