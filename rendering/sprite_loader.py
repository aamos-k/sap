"""Procedurally generates and caches image sprites for player and enemy characters.

On first use, sprites are built as Pygame Surfaces and saved as PNG files under
assets/sprites/.  If a PNG already exists on disk (e.g. replaced with custom art)
it is loaded from disk instead.

Sprite coordinate convention for limb sprites
----------------------------------------------
The template is drawn VERTICALLY with the attachment point (shoulder / hip) at
the TOP and the tip (hand / foot) at the BOTTOM.  draw_character rotates each
sprite so its bottom aligns with the limb tip.
"""
from __future__ import annotations
import os
import pygame

_ASSETS = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sprites')

_cache: dict[str, pygame.Surface] = {}

# ── Public API ─────────────────────────────────────────────────────────────────

def get(name: str) -> pygame.Surface:
    """Return the named sprite surface; generates all sprites on first call."""
    if not _cache:
        _init()
    return _cache[name]


# ── Initialisation ─────────────────────────────────────────────────────────────

def _init() -> None:
    os.makedirs(_ASSETS, exist_ok=True)
    generators = {
        'player_head':  _player_head,
        'player_torso': _player_torso,
        'player_arm':   _player_arm,
        'player_leg':   _player_leg,
        'enemy_head':   _enemy_head,
        'enemy_torso':  _enemy_torso,
        'enemy_arm':    _enemy_arm,
        'enemy_leg':    _enemy_leg,
        'slime_head':   _slime_head,
        'slime_torso':  _slime_torso,
        'slime_arm':    _slime_arm,
        'slime_leg':    _slime_leg,
    }
    for name, gen in generators.items():
        path = os.path.join(_ASSETS, f'{name}.png')
        if os.path.exists(path):
            _cache[name] = pygame.image.load(path).convert_alpha()
        else:
            surf = gen()
            pygame.image.save(surf, path)
            _cache[name] = surf


# ── Helpers ────────────────────────────────────────────────────────────────────

def _blank(w: int, h: int) -> pygame.Surface:
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    return s


def _shade(base: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(c * factor))) for c in base)  # type: ignore[return-value]


# ── Player colour palette ──────────────────────────────────────────────────────

_PS  = (150, 162, 178)   # steel
_PSD = ( 90, 100, 115)   # dark steel
_PSL = (195, 208, 222)   # light steel / highlight
_PSK = (210, 188, 158)   # skin tone
_PO  = ( 55,  60,  72)   # outline
_PEY = (255, 220, 100)   # eye glow (amber visor)


def _player_head() -> pygame.Surface:
    w, h = 18, 20
    s = _blank(w, h)

    # Helmet dome
    pygame.draw.ellipse(s, _PS, (1, 0, 16, 14))
    pygame.draw.ellipse(s, _PSL, (3, 1, 8, 5))          # highlight patch
    pygame.draw.line(s, _PSD, (1, 7), (16, 7), 1)       # helmet rim

    # Visor slot (dark bar with amber eye glints)
    pygame.draw.rect(s, _PSD, (3, 7, 12, 5))
    pygame.draw.circle(s, _PEY, (6, 9), 2)
    pygame.draw.circle(s, _PEY, (12, 9), 2)
    pygame.draw.circle(s, (255, 255, 200), (6, 8), 1)   # bright centre
    pygame.draw.circle(s, (255, 255, 200), (12, 8), 1)

    # Lower face guard
    pygame.draw.rect(s, _PSK, (3, 12, 12, 6))
    pygame.draw.line(s, _PSD, (3, 15), (14, 15), 1)     # chin crease
    pygame.draw.rect(s, _PS,  (3, 17, 12, 2))            # chin plate

    # Outlines
    pygame.draw.ellipse(s, _PO, (1, 0, 16, 14), 1)
    pygame.draw.rect(s, _PO, (3, 12, 12, 6), 1)
    return s


def _player_torso() -> pygame.Surface:
    w, h = 22, 18
    s = _blank(w, h)

    # Breastplate body
    pygame.draw.rect(s, _PS, (2, 0, 18, 18), border_radius=3)

    # Chest highlight band
    pygame.draw.line(s, _PSL, (4, 2), (4, 10), 1)
    pygame.draw.line(s, _PSL, (5, 2), (5, 10), 1)

    # Centre line
    pygame.draw.line(s, _PSD, (11, 1), (11, 17), 1)

    # Pauldron flanges at top corners
    pygame.draw.rect(s, _PSD, (0, 0, 4, 5), border_radius=1)
    pygame.draw.rect(s, _PSD, (18, 0, 4, 5), border_radius=1)

    # Belt
    pygame.draw.rect(s, _PSD, (2, 13, 18, 4))
    pygame.draw.line(s, _PSL, (10, 14), (10, 16), 1)    # belt buckle

    # Outline
    pygame.draw.rect(s, _PO, (2, 0, 18, 18), 1, border_radius=3)
    return s


def _player_arm() -> pygame.Surface:
    """8×50 px, attachment at top, hand at bottom."""
    w, h = 8, 50
    s = _blank(w, h)

    # Shoulder cap (rows 0-7)
    pygame.draw.ellipse(s, _PSD, (0, 0, w, 10))
    pygame.draw.line(s, _PSL, (2, 2), (5, 2), 1)

    # Upper arm (rows 7-24)
    pygame.draw.rect(s, _PS, (1, 7, 6, 17), border_radius=2)
    pygame.draw.line(s, _PSL, (2, 8), (2, 22), 1)

    # Elbow guard (rows 24-30)
    pygame.draw.rect(s, _PSD, (0, 24, w, 7), border_radius=2)
    pygame.draw.line(s, _PSL, (1, 25), (6, 25), 1)

    # Forearm (rows 30-42)
    pygame.draw.rect(s, _PS, (1, 30, 5, 12), border_radius=1)
    pygame.draw.line(s, _PSL, (2, 31), (2, 40), 1)

    # Gauntlet / fist (rows 42-50)
    pygame.draw.rect(s, _PS, (0, 42, 7, 8), border_radius=2)
    pygame.draw.line(s, _PSD, (1, 44), (5, 44), 1)   # knuckle line
    pygame.draw.line(s, _PSD, (1, 46), (5, 46), 1)

    # Outlines
    pygame.draw.ellipse(s, _PO, (0, 0, w, 10), 1)
    pygame.draw.rect(s, _PO, (1, 7, 6, 17), 1, border_radius=2)
    pygame.draw.rect(s, _PO, (1, 30, 5, 12), 1, border_radius=1)
    pygame.draw.rect(s, _PO, (0, 42, 7, 8), 1, border_radius=2)
    return s


def _player_leg() -> pygame.Surface:
    """10×50 px, attachment at top, boot at bottom."""
    w, h = 10, 50
    s = _blank(w, h)

    # Hip joint (rows 0-6)
    pygame.draw.ellipse(s, _PSD, (1, 0, 8, 8))

    # Thigh (rows 6-24)
    pygame.draw.rect(s, _PS, (1, 6, 8, 18), border_radius=2)
    pygame.draw.line(s, _PSL, (2, 7), (2, 22), 1)

    # Knee plate (rows 24-31)
    pygame.draw.rect(s, _PSD, (0, 24, w, 8), border_radius=2)
    pygame.draw.ellipse(s, _PSL, (2, 25, 6, 4))

    # Greave / shin (rows 31-41)
    pygame.draw.rect(s, _PS, (1, 31, 7, 10), border_radius=1)
    pygame.draw.line(s, _PSL, (2, 32), (2, 39), 1)

    # Boot (rows 41-50)
    pygame.draw.rect(s, _PSD, (0, 41, 10, 9), border_radius=3)
    pygame.draw.rect(s, _PO, (0, 41, 10, 9), 1, border_radius=3)
    pygame.draw.line(s, _PSL, (1, 43), (7, 43), 1)

    # Outlines
    pygame.draw.ellipse(s, _PO, (1, 0, 8, 8), 1)
    pygame.draw.rect(s, _PO, (1, 6, 8, 18), 1, border_radius=2)
    pygame.draw.rect(s, _PO, (1, 31, 7, 10), 1, border_radius=1)
    return s


# ── Enemy colour palette ───────────────────────────────────────────────────────

_EB  = (195,  78,  32)   # base orange
_EBD = (125,  42,  12)   # dark
_EBL = (230, 118,  58)   # light
_EEY = (255, 210,   0)   # eye glow
_EO  = ( 65,  18,   5)   # outline


def _enemy_head() -> pygame.Surface:
    w, h = 22, 22
    s = _blank(w, h)

    # Horn stumps
    pygame.draw.polygon(s, _EBD, [(4, 8), (3, 0), (8, 6)])
    pygame.draw.polygon(s, _EBD, [(18, 8), (19, 0), (14, 6)])

    # Head blob
    pygame.draw.ellipse(s, _EB, (1, 5, 20, 16))
    pygame.draw.ellipse(s, _EBL, (3, 6, 8, 6))          # highlight

    # Eyes (glowing yellow)
    pygame.draw.circle(s, _EEY, (7, 12), 3)
    pygame.draw.circle(s, _EEY, (15, 12), 3)
    pygame.draw.circle(s, (255, 255, 140), (7, 11), 1)  # bright pupil
    pygame.draw.circle(s, (255, 255, 140), (15, 11), 1)

    # Mouth
    pygame.draw.line(s, _EBD, (7, 18), (15, 18), 2)
    # Fangs
    for fx in (9, 13):
        pygame.draw.line(s, (230, 225, 210), (fx, 18), (fx, 20), 1)

    # Outline
    pygame.draw.ellipse(s, _EO, (1, 5, 20, 16), 1)
    return s


def _enemy_torso() -> pygame.Surface:
    w, h = 26, 20
    s = _blank(w, h)

    # Chunky trapezoid body (wider at top)
    pts = [(1, 0), (25, 0), (22, 20), (4, 20)]
    pygame.draw.polygon(s, _EB, pts)
    pygame.draw.polygon(s, _EBL, [(3, 1), (12, 1), (10, 7), (3, 7)])  # highlight

    # Belly scales (dark diamond shapes)
    for yi in range(2):
        for xi in range(2):
            cx = 8 + xi * 9
            cy = 7 + yi * 7
            pygame.draw.polygon(s, _EBD,
                                [(cx, cy-3), (cx+3, cy), (cx, cy+3), (cx-3, cy)])

    # Outline
    pygame.draw.polygon(s, _EO, pts, 1)
    return s


def _enemy_arm() -> pygame.Surface:
    """10×50 px, attachment at top, claws at bottom."""
    w, h = 10, 50
    s = _blank(w, h)

    # Shoulder mass (rows 0-8)
    pygame.draw.ellipse(s, _EBD, (0, 0, w, 10))
    pygame.draw.line(s, _EBL, (2, 2), (7, 2), 1)

    # Upper arm (rows 8-26, thick)
    pygame.draw.rect(s, _EB, (1, 8, 8, 18), border_radius=2)
    pygame.draw.line(s, _EBL, (2, 9), (2, 24), 1)

    # Elbow protrusion
    pygame.draw.ellipse(s, _EBD, (0, 25, w, 9))
    pygame.draw.line(s, _EBL, (1, 26), (8, 26), 1)

    # Forearm (rows 33-43, tapers)
    pygame.draw.rect(s, _EB, (2, 33, 6, 10), border_radius=1)

    # Claws (rows 43-50)
    pygame.draw.line(s, _EBD, (1, 43), (0, 50), 2)
    pygame.draw.line(s, _EBD, (5, 43), (4, 50), 2)
    pygame.draw.line(s, _EBD, (8, 43), (9, 50), 2)

    # Outlines
    pygame.draw.ellipse(s, _EO, (0, 0, w, 10), 1)
    pygame.draw.rect(s, _EO, (1, 8, 8, 18), 1, border_radius=2)
    pygame.draw.rect(s, _EO, (2, 33, 6, 10), 1, border_radius=1)
    return s


def _enemy_leg() -> pygame.Surface:
    """12×50 px, attachment at top, clawed foot at bottom."""
    w, h = 12, 50
    s = _blank(w, h)

    # Hip mass (rows 0-8)
    pygame.draw.ellipse(s, _EBD, (1, 0, 10, 9))

    # Thigh (rows 8-26)
    pygame.draw.rect(s, _EB, (1, 8, 10, 18), border_radius=3)
    pygame.draw.line(s, _EBL, (2, 9), (2, 24), 1)

    # Knee spike
    pygame.draw.polygon(s, _EBD, [(6, 26), (w, 32), (0, 32)])
    pygame.draw.line(s, _EBL, (5, 27), (6, 27), 1)

    # Shin (rows 32-42)
    pygame.draw.rect(s, _EB, (2, 32, 8, 10), border_radius=2)
    pygame.draw.line(s, _EBL, (3, 33), (3, 40), 1)

    # Foot (rows 42-47)
    pygame.draw.rect(s, _EBD, (1, 42, 10, 6), border_radius=2)
    # Toe claws
    pygame.draw.line(s, _EBD, (2, 47), (1, 50), 2)
    pygame.draw.line(s, _EBD, (6, 47), (5, 50), 2)
    pygame.draw.line(s, _EBD, (10, 47), (10, 50), 2)

    # Outlines
    pygame.draw.ellipse(s, _EO, (1, 0, 10, 9), 1)
    pygame.draw.rect(s, _EO, (1, 8, 10, 18), 1, border_radius=3)
    pygame.draw.rect(s, _EO, (2, 32, 8, 10), 1, border_radius=2)
    pygame.draw.rect(s, _EO, (1, 42, 10, 6), 1, border_radius=2)
    return s


# ── Slime mold colour palette ──────────────────────────────────────────────────

_SB  = ( 50, 140,  40)   # base green
_SBD = ( 25,  85,  18)   # dark green
_SBL = (110, 200,  65)   # light / highlight
_SEY = (185, 255,  20)   # eye glow (yellow-green)
_SO  = ( 15,  50,  10)   # outline


def _slime_head() -> pygame.Surface:
    w, h = 20, 20
    s = _blank(w, h)

    # Main blob
    pygame.draw.ellipse(s, _SB, (1, 2, 18, 15))

    # Surface highlight bubbles
    pygame.draw.circle(s, _SBL, (7, 5), 3)
    pygame.draw.circle(s, _SBL, (13, 5), 2)

    # Glowing eyes
    pygame.draw.circle(s, _SEY, (6, 11), 3)
    pygame.draw.circle(s, _SEY, (14, 11), 3)
    pygame.draw.circle(s, (220, 255, 140), (6, 10), 1)
    pygame.draw.circle(s, (220, 255, 140), (14, 10), 1)

    # Drip at bottom
    pygame.draw.ellipse(s, _SBD, (7, 16, 6, 4))

    # Outline
    pygame.draw.ellipse(s, _SO, (1, 2, 18, 15), 1)
    return s


def _slime_torso() -> pygame.Surface:
    w, h = 20, 16
    s = _blank(w, h)

    # Main blob
    pygame.draw.ellipse(s, _SB, (0, 1, 20, 14))

    # Highlight patch
    pygame.draw.ellipse(s, _SBL, (2, 2, 8, 5))

    # Internal dark bubbles for texture
    pygame.draw.circle(s, _SBD, (8, 9), 3)
    pygame.draw.circle(s, _SBD, (14, 8), 2)
    pygame.draw.circle(s, _SBD, (5, 10), 2)

    # Outline
    pygame.draw.ellipse(s, _SO, (0, 1, 20, 14), 1)
    return s


def _slime_arm() -> pygame.Surface:
    """8×50 px pseudopod, attachment at top, drip tip at bottom."""
    w, h = 8, 50
    s = _blank(w, h)

    # Tapered pseudopod body
    pygame.draw.polygon(s, _SB, [(0, 0), (w, 0), (6, 44), (4, 50), (2, 44)])

    # Highlight strip along leading edge
    pygame.draw.polygon(s, _SBL, [(1, 1), (4, 1), (3, 18), (1, 18)])

    # Segment rings
    for y in range(10, 44, 10):
        half = max(1, int(3 - y * 0.03))
        pygame.draw.line(s, _SBD, (4 - half, y), (4 + half, y), 1)

    # Tip highlight
    pygame.draw.circle(s, _SBL, (4, 49), 1)

    # Outline
    pygame.draw.polygon(s, _SO, [(0, 0), (w, 0), (6, 44), (4, 50), (2, 44)], 1)
    return s


def _slime_leg() -> pygame.Surface:
    """10×50 px pseudopod leg, attachment at top, drip tip at bottom."""
    w, h = 10, 50
    s = _blank(w, h)

    # Slightly wider pseudopod than arm
    pygame.draw.polygon(s, _SB, [(0, 0), (w, 0), (7, 44), (5, 50), (3, 44)])

    # Highlight strip
    pygame.draw.polygon(s, _SBL, [(1, 1), (5, 1), (4, 20), (1, 20)])

    # Segment rings
    for y in range(10, 44, 10):
        half = max(1, int(4 - y * 0.03))
        pygame.draw.line(s, _SBD, (5 - half, y), (5 + half, y), 1)

    # Tip highlight
    pygame.draw.circle(s, _SBL, (5, 49), 1)

    # Outline
    pygame.draw.polygon(s, _SO, [(0, 0), (w, 0), (7, 44), (5, 50), (3, 44)], 1)
    return s
