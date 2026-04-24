from __future__ import annotations
import pygame
from entities.character import Character
from entities.limb import LimbId
from game.turn_manager import TurnManager, TurnState
from rendering.camera import Camera

# Colours
PLAYER_LIMB   = (220, 220, 220)
ENEMY_LIMB    = (220, 100,  50)
SELECTED_LIMB = (255, 230,   0)
ANCHORED_TIP  = ( 60, 200,  80)
FREE_TIP      = (200,  60,  60)
BODY_COLOUR   = (180, 180, 180)
ENEMY_BODY    = (200,  80,  40)
HEAD_PLAYER   = (230, 230, 200)
HEAD_ENEMY    = (220, 120,  60)
HP_GREEN      = ( 60, 200,  80)
HP_RED        = (200,  60,  60)
HP_BG         = ( 50,  50,  50)

HP_BAR_W = 40
HP_BAR_H = 5


def draw_character(screen: pygame.Surface, camera: Camera,
                   char: Character, tm: TurnManager | None) -> None:
    if not char.alive:
        return

    bx, by = camera.world_to_screen(char.body_x, char.body_y)
    is_player = char.is_player

    base_col = PLAYER_LIMB if is_player else ENEMY_LIMB
    head_col  = HEAD_PLAYER if is_player else HEAD_ENEMY
    body_col  = BODY_COLOUR if is_player else ENEMY_BODY

    for limb_id, limb in char.limbs.items():
        tx, ty = camera.world_to_screen(limb.tip_x, limb.tip_y)

        # Line colour
        if (is_player and tm is not None
                and tm.state in (TurnState.PLAYER_SELECT_TARGET,)
                and tm.selected_limb == limb_id):
            col = SELECTED_LIMB
            width = 3
        else:
            col = base_col
            width = 2

        pygame.draw.line(screen, col, (bx, by), (tx, ty), width)

        # Tip marker
        tip_col = ANCHORED_TIP if limb.anchored else FREE_TIP
        if limb.anchored:
            pygame.draw.circle(screen, tip_col, (tx, ty), 4)
        else:
            pygame.draw.circle(screen, tip_col, (tx, ty), 4, 1)

    # Body circle
    pygame.draw.circle(screen, body_col, (bx, by), 6)
    # Head
    pygame.draw.circle(screen, head_col, (bx, by - 14), 8)

    # HP bar in world space (above head)
    _draw_hp_bar(screen, bx, by - 28, char.hp, char.max_hp)


def _draw_hp_bar(screen: pygame.Surface,
                 cx: int, cy: int, hp: int, max_hp: int) -> None:
    x = cx - HP_BAR_W // 2
    y = cy - HP_BAR_H
    pygame.draw.rect(screen, HP_BG, (x, y, HP_BAR_W, HP_BAR_H))
    fill_w = int(HP_BAR_W * hp / max_hp)
    col = HP_GREEN if hp > max_hp // 3 else HP_RED
    if fill_w > 0:
        pygame.draw.rect(screen, col, (x, y, fill_w, HP_BAR_H))
