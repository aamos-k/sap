from __future__ import annotations
import random
from cave.generator import generate_cave, generate_extension
from cave.grid import CaveGrid
from entities.player import Player
from entities.enemy import Enemy
from entities.slime_mold import SlimeMold
from entities.loot_bag import LootBag
from entities.spear import Spear, SPEAR_DAMAGE
from entities.limb import LimbId
from game.physics import (resolve_anchoring, apply_gravity,
                           clamp_limb_to_open, check_collision_damage)
from game.turn_manager import TurnManager, TurnState
from rendering.camera import Camera

ENEMY_THINK_TICKS = 18
TILE_SIZE         = 16
_DT               = 1.0 / 60

# Extend the cave when the player is this close to the grid bottom
_EXTEND_TRIGGER_PX = 30 * 16   # 30 tiles
_EXTENSION_TILES   = 160        # tile-rows added per extension


class World:
    def __init__(self, seed: int = 0):
        self.seed = seed
        self._rng = random.Random(seed + 99)
        self._ext_rng = random.Random(seed + 7777)
        self._extension_count = 0
        # flag read by CaveRenderer to detect grid growth
        self.cave_dirty = False

        grid, bulb, room_centres = generate_cave(width=400, height=80, seed=seed)
        self.grid: CaveGrid = grid

        bx, by = grid.tile_to_world(*bulb)
        self.player = Player.create(bx, by - TILE_SIZE)

        for lid in (LimbId.LEFT_LEG, LimbId.RIGHT_LEG):
            limb = self.player.get_limb(lid)
            clamp_limb_to_open(limb, grid)
            resolve_anchoring(limb, grid)
        self.player.compute_body_position()

        self.enemies: list[Enemy | SlimeMold] = []
        self._spawn_enemies_in_rooms(room_centres, skip_first=3)

        self.bags: list[LootBag] = []
        self._spawn_bags_in_rooms(room_centres)

        self.spear = Spear(x=self.player.body_x, y=self.player.body_y)

        self.turn_manager = TurnManager(player=self.player, enemies=self.enemies)
        self.camera = Camera(
            x=self.player.body_x - 640,
            y=self.player.body_y - 360,
            screen_w=1280,
            screen_h=720,
        )
        self._enemy_think_timer = 0

    # ── entity iteration ──────────────────────────────────────────────────────

    @property
    def entities(self):
        yield self.player
        yield from self.enemies

    # ── main tick ─────────────────────────────────────────────────────────────

    def tick(self) -> None:
        tm = self.turn_manager
        tm.tick_flash()

        if tm.state == TurnState.ENEMY_THINK:
            self._enemy_think_timer += 1
            if self._enemy_think_timer >= ENEMY_THINK_TICKS:
                self._enemy_think_timer = 0
                self._run_enemy_turns()

        # Soft-body slimes simulate every frame regardless of turn state
        self._step_slimes()

        self._update_bags()
        self._update_spear()
        self._maybe_extend_cave()
        self.camera.follow(self.player.body_x, self.player.body_y)

    # ── player action ─────────────────────────────────────────────────────────

    def apply_player_move(self, target_wx: float, target_wy: float) -> bool:
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
        self._maybe_extend_cave()
        apply_gravity(self.player, self.grid)

        # Limb-based damage against regular enemies
        check_collision_damage(self.player, [e for e in self.enemies
                                             if not isinstance(e, SlimeMold)])
        # Particle-overlap damage against slimes
        for enemy in self.enemies:
            if isinstance(enemy, SlimeMold) and enemy.alive:
                # Check if any player limb tip is inside the slime blob
                from game.physics import HIT_RADIUS
                for limb_obj in self.player.limbs.values():
                    if enemy.overlaps_body(limb_obj.tip_x, limb_obj.tip_y):
                        enemy.take_damage(1)
                        break

        for enemy in self.enemies:
            if not enemy.alive and all(not e.alive for e in self.enemies):
                tm.set_game_over("player")
                return True

        tm.advance_to_enemy()
        return True

    def apply_throw(self, target_wx: float, target_wy: float) -> bool:
        tm = self.turn_manager
        if not self.spear.held:
            tm.set_flash("No spear!")
            return False
        self.spear.throw(self.player.body_x, self.player.body_y, target_wx, target_wy)
        tm.advance_to_enemy()
        return True

    # ── enemy turns ───────────────────────────────────────────────────────────

    def _run_enemy_turns(self) -> None:
        tm = self.turn_manager
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            if isinstance(enemy, SlimeMold):
                # Soft-body slimes: damage check via particle proximity
                if enemy.overlaps_body(self.player.body_x, self.player.body_y):
                    self.player.take_damage(1)
                    if not self.player.alive:
                        tm.set_game_over("enemy")
                        return
                continue

            # Regular limb-based enemy
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

    # ── slime physics ─────────────────────────────────────────────────────────

    def _step_slimes(self) -> None:
        for enemy in self.enemies:
            if isinstance(enemy, SlimeMold) and enemy.alive:
                enemy.step(_DT, self.grid,
                           self.player.body_x, self.player.body_y)

    # ── bag physics ───────────────────────────────────────────────────────────

    def _player_limb_tips(self) -> list[tuple[float, float]]:
        return [(limb.tip_x, limb.tip_y) for limb in self.player.limbs.values()]

    def _update_bags(self) -> None:
        tips = self._player_limb_tips()
        for bag in self.bags:
            bag.check_spill(tips)
            bag.update(self.grid, _DT)

    # ── spear physics & retrieval ─────────────────────────────────────────────

    def _update_spear(self) -> None:
        spear = self.spear
        spear.update(self.grid, _DT)

        if spear.in_flight:
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if spear.check_hit(enemy):
                    enemy.take_damage(SPEAR_DAMAGE)
                    spear.in_flight = False  # embeds in first enemy hit
                    if all(not e.alive for e in self.enemies):
                        self.turn_manager.set_game_over("player")
                    break
        elif not spear.held:
            tips = self._player_limb_tips()
            if spear.check_retrieve(tips):
                self.turn_manager.set_flash("Spear retrieved!")

    # ── infinite cave extension ───────────────────────────────────────────────

    def _maybe_extend_cave(self) -> None:
        grid_bottom_px = self.grid.height * TILE_SIZE
        if self.player.body_y > grid_bottom_px - _EXTEND_TRIGGER_PX:
            self._extend_cave()

    def _extend_cave(self) -> None:
        self.grid.extend_down(_EXTENSION_TILES)

        new_rooms: list[tuple[int, int]] = []
        generate_extension(self.grid, self._ext_rng, new_rooms, _EXTENSION_TILES)
        self._extension_count += 1
        self.cave_dirty = True

        self._spawn_enemies_in_rooms(new_rooms, skip_first=1)
        self._spawn_bags_in_rooms(new_rooms)

    # ── spawning helpers ──────────────────────────────────────────────────────

    def _spawn_enemies_in_rooms(self, room_centres: list[tuple[int, int]],
                                skip_first: int = 0) -> None:
        for i, room_centre in enumerate(room_centres):
            if i < skip_first:
                continue
            ex, ey = self.grid.tile_to_world(*room_centre)
            count = 1
            for j in range(count):
                offset_x = (j - (count - 1) / 2) * 26
                spawn_x = ex + offset_x
                spawn_y = ey - TILE_SIZE
                if self._rng.random() < 0.45:
                    enemy: Enemy | SlimeMold = SlimeMold.create(spawn_x, spawn_y)
                else:
                    enemy = Enemy.create(spawn_x, spawn_y)
                    for lid in (LimbId.LEFT_LEG, LimbId.RIGHT_LEG):
                        limb = enemy.get_limb(lid)
                        clamp_limb_to_open(limb, self.grid)
                        resolve_anchoring(limb, self.grid)
                    enemy.compute_body_position()
                self.enemies.append(enemy)

    def _spawn_bags_in_rooms(self, room_centres: list[tuple[int, int]]) -> None:
        for room_centre in room_centres:
            bx_r, by_r = self.grid.tile_to_world(*room_centre)
            bag_rng = random.Random(self._rng.randint(0, 2 ** 32))
            self.bags.append(LootBag(bx_r, by_r - TILE_SIZE, rng=bag_rng))
