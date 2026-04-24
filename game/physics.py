from __future__ import annotations
import math
from entities.limb import Limb, LimbId
from entities.character import Character
from cave.grid import CaveGrid

GRAVITY = 2          # tiles per turn
TERMINAL_VEL = 20    # tiles per turn cap
HIT_RADIUS = 14      # pixels — limb tip hits if closer than this to enemy body
BODY_RADIUS = 8      # pixels — collision radius of the body circle


def resolve_anchoring(limb: Limb, grid: CaveGrid) -> None:
    """Set limb.anchored based on whether its tip is adjacent to solid rock."""
    limb.anchored = would_anchor(limb.id, limb.tip_x, limb.tip_y, grid)


def would_anchor(limb_id: LimbId, wx: float, wy: float, grid: CaveGrid) -> bool:
    tx, ty = grid.world_to_tile(wx, wy)
    ts = grid.TILE_SIZE

    # Tip must not be inside solid
    if grid.is_solid(tx, ty):
        return False

    if limb_id in (LimbId.LEFT_LEG, LimbId.RIGHT_LEG):
        # Legs anchor when tile directly below is solid
        return grid.is_solid(tx, ty + 1)
    else:
        # Arms anchor when any neighbouring tile is solid
        for nx, ny in grid.neighbours8(tx, ty):
            if grid.is_solid(nx, ny):
                return True
        return False


def apply_gravity(character: Character, grid: CaveGrid) -> None:
    """Apply gravity to character if no limbs are anchored."""
    if character.anchored_count() > 0:
        character.vel_y = 0.0
        return

    ts = grid.TILE_SIZE
    character.vel_y = min(character.vel_y + GRAVITY * ts, TERMINAL_VEL * ts)

    # Sweep downward in BODY_RADIUS-sized steps so fast falls never tunnel
    # through floors.  Step (8 px) < TILE_SIZE (16 px), so any 1-tile-thick
    # floor is guaranteed to be detected before the body centre crosses it.
    step = BODY_RADIUS
    remaining = character.vel_y          # always ≥ 0; gravity is downward only
    new_y = character.body_y

    while remaining > 0:
        advance = min(step, remaining)
        candidate = new_y + advance
        btx, bty = grid.world_to_tile(character.body_x, candidate + BODY_RADIUS)
        if grid.is_solid(btx, bty):
            new_y = bty * ts - BODY_RADIUS  # snap body flush above tile top
            character.vel_y = 0.0
            remaining = 0
            break
        new_y = candidate
        remaining -= advance

    actual_dy = new_y - character.body_y
    character.body_y = new_y

    # Drag unanchored limb tips and immediately clamp them back to open space
    # so they never end up stuck inside rock (which would block re-anchoring).
    for limb in character.limbs.values():
        if not limb.anchored:
            limb.tip_y += actual_dy
            clamp_limb_to_open(limb, grid)


def clamp_limb_to_open(limb: Limb, grid: CaveGrid) -> None:
    """If limb tip landed inside solid, BFS-snap to nearest open tile centre."""
    tx, ty = grid.world_to_tile(limb.tip_x, limb.tip_y)
    if grid.is_solid(tx, ty):
        result = grid.snap_to_open(tx, ty)
        if result:
            wx, wy = grid.tile_to_world(*result)
            limb.tip_x, limb.tip_y = wx, wy


def check_collision_damage(attacker: Character, targets: list[Character]) -> None:
    """Deal 1 damage to any target whose body is within HIT_RADIUS of an attacker limb tip."""
    for limb in attacker.limbs.values():
        for target in targets:
            if not target.alive:
                continue
            dist = math.hypot(limb.tip_x - target.body_x, limb.tip_y - target.body_y)
            if dist < HIT_RADIUS:
                target.take_damage(1)


def validate_limb_move(character: Character, limb: Limb, target_wx: float, target_wy: float) -> bool:
    """Return True if the target position is within limb reach of the body."""
    dx = target_wx - character.body_x
    dy = target_wy - character.body_y
    return math.hypot(dx, dy) <= limb.length
