from __future__ import annotations
import math
import pygame
from game.world import World
from game.turn_manager import TurnState
from rendering.cave_renderer import CaveRenderer
from rendering.character_renderer import draw_character
from rendering.hud import HUD

BG = (12, 10, 14)

# Rope colours
_ROPE_LINE_PENDING  = (200, 160,  70)
_ROPE_LINE_DONE     = ( 90,  70,  35)
_ROPE_PT_CURRENT    = (255, 210,  50)
_ROPE_PT_PENDING    = (200, 160,  70)
_ROPE_PT_DONE       = ( 90,  70,  35)

# Loot bag colours
_BAG_BODY   = (139, 100,  45)
_BAG_DARK   = ( 90,  58,  18)
_BAG_TIE    = ( 72,  46,  14)
_BAG_HILIT  = (185, 148,  72)

# Coin colours
_COIN_GOLD   = (255, 215,   0)
_COIN_BRIGHT = (255, 244, 120)
_COIN_SHADOW = (175, 140,   0)

# Spear colours
_SPEAR_SHAFT = (180, 140,  70)
_SPEAR_TIP   = (200, 200, 220)
_SPEAR_GLOW  = (255, 220,  80)   # ring when on ground (retrievable)


class Renderer:
    def __init__(self, screen: pygame.Surface, world: World) -> None:
        self.screen = screen
        self.world = world
        self.cave_renderer = CaveRenderer(world.grid)
        sw, sh = screen.get_size()
        self.hud = HUD(sw, sh)
        self._reach_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)

    def draw_frame(self) -> None:
        screen = self.screen
        world = self.world
        tm = world.turn_manager
        camera = world.camera
        mouse_pos = pygame.mouse.get_pos()

        screen.fill(BG)
        self.cave_renderer.draw(screen, camera)

        # Draw rope waypoints (below characters)
        self._draw_rope(screen, camera)

        # Draw loot bags and loose coins (below characters)
        self._draw_bags(screen, camera)

        # Draw spear in world space (when not held)
        self._draw_spear(screen, camera)

        # Draw reach indicator when player is selecting a target
        if tm.state == TurnState.PLAYER_SELECT_TARGET and tm.selected_limb is not None:
            limb = world.player.get_limb(tm.selected_limb)
            bsx, bsy = camera.world_to_screen(world.player.body_x, world.player.body_y)
            reach_px = int(limb.length * camera.zoom)
            self._reach_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(self._reach_surface, (255, 230, 0, 35),
                                (bsx, bsy), reach_px)
            pygame.draw.circle(self._reach_surface, (255, 230, 0, 80),
                                (bsx, bsy), reach_px, 1)
            screen.blit(self._reach_surface, (0, 0))

        for entity in world.entities:
            draw_character(screen, camera, entity, tm)

        self.hud.draw(
            screen, tm, mouse_pos,
            seed=world.seed,
            spear=world.spear,
            depth_tiles=world.depth_tiles,
            coins=world.coins,
            player_in_shop=world.player_in_shop,
            player_hp=world.player.hp,
            player_max_hp=world.player.max_hp,
            hp_upgrade_cost=world.hp_upgrade_cost,
            reach_upgrade_cost=world.reach_upgrade_cost,
            generation=world.generation,
            total_deaths=world.total_deaths,
        )
        pygame.display.flip()

    def _draw_spear(self, screen: pygame.Surface, camera) -> None:
        spear = self.world.spear
        if spear.held:
            return
        sx, sy = camera.world_to_screen(spear.x, spear.y)
        if spear.in_flight:
            angle = math.atan2(spear.vy, spear.vx)
        else:
            angle = 0.4  # slight lean when resting on ground
        half = max(10, int(14 * camera.zoom))
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        tail = (sx - int(cos_a * half), sy - int(sin_a * half))
        tip  = (sx + int(cos_a * half), sy + int(sin_a * half))
        pygame.draw.line(screen, _SPEAR_SHAFT, tail, tip, max(2, int(3 * camera.zoom)))
        pygame.draw.circle(screen, _SPEAR_TIP, tip, max(2, int(3 * camera.zoom)))
        # Glow ring when resting on ground — signals it can be retrieved
        if not spear.in_flight:
            pygame.draw.circle(screen, _SPEAR_GLOW, (sx, sy),
                               max(8, int(10 * camera.zoom)), 1)

    def _draw_rope(self, screen: pygame.Surface, camera) -> None:
        world = self.world
        rope = world.rope_points
        if not rope:
            return
        rope_idx = world._rope_index

        # Lines between consecutive waypoints
        for i in range(len(rope) - 1):
            x1, y1 = camera.world_to_screen(*rope[i])
            x2, y2 = camera.world_to_screen(*rope[i + 1])
            col = _ROPE_LINE_DONE if i < rope_idx else _ROPE_LINE_PENDING
            pygame.draw.line(screen, col, (int(x1), int(y1)), (int(x2), int(y2)), 2)

        # Point markers
        for i, pt in enumerate(rope):
            sx, sy = int(camera.world_to_screen(*pt)[0]), int(camera.world_to_screen(*pt)[1])
            if i < rope_idx:
                pygame.draw.circle(screen, _ROPE_PT_DONE, (sx, sy), 3)
            elif i == rope_idx:
                pygame.draw.circle(screen, _ROPE_PT_CURRENT, (sx, sy), 6)
                pygame.draw.circle(screen, (255, 255, 200), (sx, sy), 6, 1)
            else:
                pygame.draw.circle(screen, _ROPE_PT_PENDING, (sx, sy), 4)

    def _draw_bags(self, screen: pygame.Surface, camera) -> None:
        for bag in self.world.bags:
            sx, sy = camera.world_to_screen(bag.x, bag.y)

            if bag.spilled:
                # Coins scattered on the ground
                for coin in bag.coins:
                    cx, cy = camera.world_to_screen(coin.x, coin.y)
                    pygame.draw.circle(screen, _COIN_GOLD, (cx, cy), 5)
                    pygame.draw.circle(screen, _COIN_BRIGHT, (cx - 1, cy - 1), 2)
                    pygame.draw.circle(screen, _COIN_SHADOW, (cx, cy), 5, 1)
                # Collapsed bag remnant
                pygame.draw.ellipse(screen, _BAG_DARK, (sx - 10, sy - 4, 20, 8))
                pygame.draw.ellipse(screen, _BAG_BODY, (sx - 9, sy - 3, 18, 6))
            else:
                # Intact bag — rounded sack body with tied neck
                pygame.draw.ellipse(screen, _BAG_BODY, (sx - 9, sy - 8, 18, 16))
                # Neck tie
                pygame.draw.rect(screen, _BAG_TIE, (sx - 3, sy - 15, 6, 8),
                                 border_radius=2)
                pygame.draw.circle(screen, _BAG_DARK, (sx, sy - 11), 3)
                # Highlight swell on body
                pygame.draw.ellipse(screen, _BAG_HILIT, (sx - 6, sy - 6, 7, 8))
                # Coin bump hint
                pygame.draw.circle(screen, _BAG_DARK, (sx + 2, sy + 2), 3, 1)
                # Outline
                pygame.draw.ellipse(screen, _BAG_DARK, (sx - 9, sy - 8, 18, 16), 1)
