from __future__ import annotations
import pygame
from game.world import World
from game.turn_manager import TurnState
from rendering.cave_renderer import CaveRenderer
from rendering.character_renderer import draw_character
from rendering.hud import HUD

BG = (12, 10, 14)


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

        self.hud.draw(screen, tm, mouse_pos)
        pygame.display.flip()
