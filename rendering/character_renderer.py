from __future__ import annotations
import math
import pygame
from entities.character import Character
from entities.limb import LimbId
from game.turn_manager import TurnManager, TurnState
from rendering.camera import Camera
from rendering import sprite_loader

SELECTED_LIMB = (255, 230,   0)
ANCHORED_TIP  = ( 60, 200,  80)
FREE_TIP      = (200,  60,  60)
HP_GREEN      = ( 60, 200,  80)
HP_RED        = (200,  60,  60)
HP_BG         = ( 50,  50,  50)

HP_BAR_W = 40
HP_BAR_H = 5

_BACK_LIMBS  = (LimbId.LEFT_ARM,  LimbId.LEFT_LEG)
_FRONT_LIMBS = (LimbId.RIGHT_ARM, LimbId.RIGHT_LEG)

# Slime palette
_SLIME_FILL    = ( 30, 160,  60,  200)  # translucent green interior
_SLIME_SKIN    = ( 50, 220,  90)        # bright outline / skin
_SLIME_HILIT   = (160, 255, 180,  140)  # specular highlight
_SLIME_NUCLEUS = ( 20, 100,  40)        # dark nucleus dot


def draw_character(screen: pygame.Surface, camera: Camera,
                   char, tm: TurnManager | None) -> None:
    if not char.alive:
        return

    # Dispatch to soft-body renderer for slimes
    from entities.slime_mold import SlimeMold
    if isinstance(char, SlimeMold):
        _draw_slime(screen, camera, char)
        return

    # ── regular limb-based character ─────────────────────────────────────────
    bx, by = camera.world_to_screen(char.body_x, char.body_y)
    pfx = getattr(char, 'sprite_prefix', 'player' if char.is_player else 'enemy')

    selected: LimbId | None = None
    if (char.is_player and tm is not None
            and tm.state == TurnState.PLAYER_SELECT_TARGET):
        selected = tm.selected_limb

    for lid in _BACK_LIMBS:
        limb = char.limbs[lid]
        tx, ty = camera.world_to_screen(limb.tip_x, limb.tip_y)
        kind = 'arm' if lid in (LimbId.LEFT_ARM, LimbId.RIGHT_ARM) else 'leg'
        _draw_limb_sprite(screen, sprite_loader.get(f'{pfx}_{kind}'), bx, by, tx, ty)

    torso = sprite_loader.get(f'{pfx}_torso')
    screen.blit(torso, torso.get_rect(center=(bx, by)))

    for lid in _FRONT_LIMBS:
        limb = char.limbs[lid]
        tx, ty = camera.world_to_screen(limb.tip_x, limb.tip_y)
        kind = 'arm' if lid in (LimbId.LEFT_ARM, LimbId.RIGHT_ARM) else 'leg'
        _draw_limb_sprite(screen, sprite_loader.get(f'{pfx}_{kind}'), bx, by, tx, ty)

    head = sprite_loader.get(f'{pfx}_head')
    screen.blit(head, head.get_rect(center=(bx, by - 16)))

    for lid, limb in char.limbs.items():
        tx, ty = camera.world_to_screen(limb.tip_x, limb.tip_y)
        if lid == selected:
            pygame.draw.circle(screen, SELECTED_LIMB, (tx, ty), 6)
            pygame.draw.circle(screen, SELECTED_LIMB, (tx, ty), 6, 2)
        elif limb.anchored:
            pygame.draw.circle(screen, ANCHORED_TIP, (tx, ty), 4)
        else:
            pygame.draw.circle(screen, FREE_TIP, (tx, ty), 4, 1)

    _draw_hp_bar(screen, bx, by - 30, char.hp, char.max_hp)


# ── soft-body slime rendering ─────────────────────────────────────────────────

def _draw_slime(screen: pygame.Surface, camera: Camera, slime) -> None:
    """Draw a soft-body slime as a filled, outlined polygon with highlights."""
    pts = [(camera.world_to_screen(p[0], p[1])) for p in slime.particles]
    if len(pts) < 3:
        return

    # Filled semi-transparent interior
    blob = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(blob, _SLIME_FILL, pts)
    screen.blit(blob, (0, 0))

    # Outer skin / outline  (2 px, opaque bright green)
    pygame.draw.polygon(screen, _SLIME_SKIN, pts, 2)

    # Specular highlight on the upper-left quarter of the blob
    bx, by = camera.world_to_screen(slime.body_x, slime.body_y)
    hilit_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    # Compute a highlight polygon: subset of particles in upper-left half
    cx_s, cy_s = bx, by
    hilit_pts = []
    for sx, sy in pts:
        # Include particles that are above and somewhat left of centre
        if sy < cy_s + 4:
            hilit_pts.append((sx, sy))
    if len(hilit_pts) >= 3:
        pygame.draw.polygon(hilit_surf, _SLIME_HILIT, hilit_pts)
        screen.blit(hilit_surf, (0, 0))

    # Dark nucleus dot at centroid
    pygame.draw.circle(screen, _SLIME_NUCLEUS, (bx, by), 4)

    # HP bar above blob
    _draw_hp_bar(screen, bx, by - int(slime.particles and
                 max(abs(p[1] - slime.body_y) for p in slime.particles) + 8 or 20),
                 slime.hp, slime.max_hp)


# ── shared helpers ────────────────────────────────────────────────────────────

def _draw_limb_sprite(screen: pygame.Surface, sprite: pygame.Surface,
                      bx: int, by: int, tx: int, ty: int) -> None:
    dx, dy = tx - bx, ty - by
    dist = math.hypot(dx, dy)
    if dist < 1:
        return

    orig_w, orig_h = sprite.get_size()
    scale = dist / orig_h
    sw = max(1, int(orig_w * scale))
    sh = max(1, int(orig_h * scale))
    scaled = pygame.transform.scale(sprite, (sw, sh))

    angle = 90.0 - math.degrees(math.atan2(dy, dx))
    rotated = pygame.transform.rotate(scaled, angle)

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
