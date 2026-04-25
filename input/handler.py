from __future__ import annotations
import pygame
from entities.limb import LimbId
from game.turn_manager import TurnState
from game.world import World
from rendering.hud import HUD

# Key → LimbId mapping
KEY_LIMB: dict[int, LimbId] = {
    pygame.K_1: LimbId.LEFT_ARM,
    pygame.K_2: LimbId.RIGHT_ARM,
    pygame.K_3: LimbId.LEFT_LEG,
    pygame.K_4: LimbId.RIGHT_LEG,
}


class InputHandler:
    def __init__(self, world: World, hud: HUD) -> None:
        self.world = world
        self.hud = hud

    def process_event(self, event: pygame.Event) -> bool:
        """Return True if the game should restart."""
        world = self.world
        tm = world.turn_manager
        camera = world.camera

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if tm.state == TurnState.PLAYER_SELECT_TARGET:
                    tm.cancel_selection()
                elif tm.state == TurnState.PLAYER_SELECT_THROW:
                    tm.cancel_throw()
                return False

            if event.key == pygame.K_t:
                if tm.state == TurnState.PLAYER_SELECT_LIMB and world.spear.held:
                    tm.start_throw()
                elif tm.state == TurnState.PLAYER_SELECT_THROW:
                    tm.cancel_throw()
                return False

            if event.key == pygame.K_r and tm.state == TurnState.GAME_OVER:
                return True  # signal restart

            # Zoom
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                camera.zoom = min(3.0, camera.zoom + 0.1)
            if event.key == pygame.K_MINUS:
                camera.zoom = max(0.3, camera.zoom - 0.1)

            # Limb hotkeys
            if tm.state == TurnState.PLAYER_SELECT_LIMB:
                lid = KEY_LIMB.get(event.key)
                if lid is not None:
                    tm.select_limb(lid)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            if tm.state == TurnState.PLAYER_SELECT_LIMB:
                if self.hud.hit_test_spear_button(pos) and world.spear.held:
                    tm.start_throw()
                    return False
                lid = self.hud.hit_test_limb_button(pos)
                if lid is not None:
                    tm.select_limb(lid)

            elif tm.state == TurnState.PLAYER_SELECT_THROW:
                wx, wy = camera.screen_to_world(*pos)
                world.apply_throw(wx, wy)

            elif tm.state == TurnState.PLAYER_SELECT_TARGET:
                # Check if clicking a limb button cancels back
                if self.hud.hit_test_limb_button(pos) is not None:
                    tm.cancel_selection()
                    return False
                wx, wy = camera.screen_to_world(*pos)
                world.apply_player_move(wx, wy)

        return False
