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
    new_y = character.body_y + character.vel_y

    # Check body's bottom edge for floor collision; this fires as soon as the
    # body circle touches a solid tile rather than waiting until the centre
    # has crossed fully into the tile.
    btx, bty = grid.world_to_tile(character.body_x, new_y + BODY_RADIUS)
    if grid.is_solid(btx, bty):
        new_y = bty * ts - BODY_RADIUS
        character.vel_y = 0.0
    else:
        # Fallback for fast falls that skip the bottom-edge check
        ctx, cty = grid.world_to_tile(character.body_x, new_y)
        if grid.is_solid(ctx, cty):
            new_y = cty * ts - BODY_RADIUS
            character.vel_y = 0.0

    dy = new_y - character.body_y
    character.body_y = new_y
    # Move un-anchored limb tips with body
    for limb in character.limbs.values():
        if not limb.anchored:
            limb.tip_y += dy


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
