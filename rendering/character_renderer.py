from __future__ import annotations
import math
import pygame
from entities.character import Character
from entities.limb import LimbId
from game.turn_manager import TurnManager, TurnState
from rendering.camera import Camera
from rendering import sprite_loader

# Tip / HP-bar colours (retained for gameplay clarity)
SELECTED_LIMB = (255, 230,   0)
ANCHORED_TIP  = ( 60, 200,  80)
FREE_TIP      = (200,  60,  60)
HP_GREEN      = ( 60, 200,  80)
HP_RED        = (200,  60,  60)
HP_BG         = ( 50,  50,  50)

HP_BAR_W = 40
HP_BAR_H = 5

# Limbs drawn first (behind torso) vs last (in front of torso)
_BACK_LIMBS  = (LimbId.LEFT_ARM,  LimbId.LEFT_LEG)
_FRONT_LIMBS = (LimbId.RIGHT_ARM, LimbId.RIGHT_LEG)


def draw_character(screen: pygame.Surface, camera: Camera,
                   char: Character, tm: TurnManager | None) -> None:
    if not char.alive:
        return

    bx, by = camera.world_to_screen(char.body_x, char.body_y)
    pfx = getattr(char, 'sprite_prefix', 'player' if char.is_player else 'enemy')

    # Determine selected limb (for tip highlight)
    selected: LimbId | None = None
    if (char.is_player and tm is not None
            and tm.state == TurnState.PLAYER_SELECT_TARGET):
        selected = tm.selected_limb

    # 1 — Back limbs (left side, drawn behind torso)
    for lid in _BACK_LIMBS:
        limb = char.limbs[lid]
        tx, ty = camera.world_to_screen(limb.tip_x, limb.tip_y)
        kind = 'arm' if lid in (LimbId.LEFT_ARM, LimbId.RIGHT_ARM) else 'leg'
        _draw_limb_sprite(screen, sprite_loader.get(f'{pfx}_{kind}'), bx, by, tx, ty)

    # 2 — Torso
    torso = sprite_loader.get(f'{pfx}_torso')
    screen.blit(torso, torso.get_rect(center=(bx, by)))

    # 3 — Front limbs (right side, drawn in front of torso)
    for lid in _FRONT_LIMBS:
        limb = char.limbs[lid]
        tx, ty = camera.world_to_screen(limb.tip_x, limb.tip_y)
        kind = 'arm' if lid in (LimbId.LEFT_ARM, LimbId.RIGHT_ARM) else 'leg'
        _draw_limb_sprite(screen, sprite_loader.get(f'{pfx}_{kind}'), bx, by, tx, ty)

    # 4 — Head
    head = sprite_loader.get(f'{pfx}_head')
    head_y = by - 16
    screen.blit(head, head.get_rect(center=(bx, head_y)))

    # 5 — Tip markers (anchored / free / selected) — keeps gameplay readability
    for lid, limb in char.limbs.items():
        tx, ty = camera.world_to_screen(limb.tip_x, limb.tip_y)
        if lid == selected:
            pygame.draw.circle(screen, SELECTED_LIMB, (tx, ty), 6)
            pygame.draw.circle(screen, SELECTED_LIMB, (tx, ty), 6, 2)
        elif limb.anchored:
            pygame.draw.circle(screen, ANCHORED_TIP, (tx, ty), 4)
        else:
            pygame.draw.circle(screen, FREE_TIP, (tx, ty), 4, 1)

    # 6 — HP bar
    _draw_hp_bar(screen, bx, by - 30, char.hp, char.max_hp)


def _draw_limb_sprite(screen: pygame.Surface, sprite: pygame.Surface,
                      bx: int, by: int, tx: int, ty: int) -> None:
    """Rotate and scale *sprite* so it spans from (bx, by) to (tx, ty)."""
    dx, dy = tx - bx, ty - by
    dist = math.hypot(dx, dy)
    if dist < 1:
        return

    orig_w, orig_h = sprite.get_size()
    # Scale height to match displayed limb length; preserve aspect ratio
    scale = dist / orig_h
    sw = max(1, int(orig_w * scale))
    sh = max(1, int(orig_h * scale))
    scaled = pygame.transform.scale(sprite, (sw, sh))

    # Sprite template points downward (+Y); rotate so bottom aligns with tip.
    # pygame.transform.rotate is counter-clockwise.
    angle = 90.0 - math.degrees(math.atan2(dy, dx))
    rotated = pygame.transform.rotate(scaled, angle)

    # Centre the rotated surface at the limb midpoint
    mid_x = (bx + tx) // 2
    mid_y = (by + ty) // 2
    screen.blit(rotated, rotated.get_rect(center=(mid_x, mid_y)))


def _draw_hp_bar(screen: pygame.Surface,
                 cx: int, cy: int, hp: int, max_hp: int) -> None:
    x = cx - HP_BAR_W // 2
    y = cy - HP_BAR_H
    pygame.draw.rect(screen, HP_BG, (x, y, HP_BAR_W, HP_BAR_H))
    fill_w = int(HP_BAR_W * hp / max_hp)
    col = HP_GREEN if hp > max_hp // 3 else HP_RED
    if fill_w > 0:
        pygame.draw.rect(screen, col, (x, y, fill_w, HP_BAR_H))
