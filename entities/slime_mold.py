"""
True 2-D soft-body slime mold.

Physics model
─────────────
• N particles arranged in a ring (Verlet integration, 4 sub-steps / frame).
• Edge springs   – nearest-neighbour pairs, stiffness SPRING_K.
• Skip-1 springs – pairs two apart;  model surface tension / skin rigidity.
• Pressure force – maintains enclosed polygon area ≈ TARGET_AREA by pushing
  every particle outward from the centroid proportionally to area deficit.
• Gravity         – constant downward acceleration.
• Chase force     – weak pull toward the player when in range.
• Wall collision  – particles that enter solid tiles are pushed back to their
  previous position (Verlet handles this cleanly).
"""
from __future__ import annotations
import math
from cave.grid import CaveGrid

# ── tuning ──────────────────────────────────────────────────────────────────
NUM_PARTICLES = 12
RADIUS        = 13.0     # resting blob radius (pixels)
GRAVITY       = 380.0    # px / s²
SPRING_K      = 1100.0   # edge-spring stiffness
SKIP_K        = 260.0    # skip-1 spring stiffness  (surface tension)
PRESSURE_K    = 1.4      # pressure coefficient
DAMPING       = 0.68     # velocity-damping factor per sub-step
SUBSTEPS      = 4        # physics sub-steps per frame
CHASE_ACCEL   = 55.0     # px / s²  toward player
CHASE_RANGE   = 280.0    # pixels  — only pull when player is this close
HIT_RADIUS    = 18       # pixels  — particle must be this close to hurt player
MAX_HP        = 6
# ─────────────────────────────────────────────────────────────────────────────


class SlimeMold:
    """Physics-driven soft body; not a Character subclass."""

    is_player: bool = False

    # ── construction ─────────────────────────────────────────────────────────

    def __init__(self, cx: float, cy: float) -> None:
        self.hp     = MAX_HP
        self.max_hp = MAX_HP
        self.alive  = True
        self.sprite_prefix = 'slime'

        n = NUM_PARTICLES
        # Particles stored as [x, y, x_old, y_old]
        self.particles: list[list[float]] = []
        for i in range(n):
            a = 2.0 * math.pi * i / n
            px = cx + RADIUS * math.cos(a)
            py = cy + RADIUS * math.sin(a)
            self.particles.append([px, py, px, py])

        self.target_area = math.pi * RADIUS * RADIUS

        # Resting lengths for the two spring families
        self._edge_rest = 2.0 * RADIUS * math.sin(math.pi / n)
        self._skip_rest = 2.0 * RADIUS * math.sin(2.0 * math.pi / n)

        self.body_x = cx
        self.body_y = cy

    @classmethod
    def create(cls, wx: float, wy: float) -> SlimeMold:
        return cls(wx, wy)

    # ── interface shared with Character/Enemy ─────────────────────────────────

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def compute_body_position(self) -> None:
        n = len(self.particles)
        if n == 0:
            return
        self.body_x = sum(p[0] for p in self.particles) / n
        self.body_y = sum(p[1] for p in self.particles) / n

    def anchored_count(self) -> int:
        return 0

    # limbs dict is empty – the soft body replaces them entirely
    @property
    def limbs(self) -> dict:
        return {}

    def get_limb(self, lid):
        return None

    def choose_move(self, grid, player_x, player_y, rng):
        """No limb-based move; physics runs every frame instead."""
        return None

    # ── soft-body physics ─────────────────────────────────────────────────────

    def step(self, dt: float, grid: CaveGrid,
             player_x: float, player_y: float) -> None:
        sub_dt = dt / SUBSTEPS
        for _ in range(SUBSTEPS):
            self._substep(sub_dt, grid, player_x, player_y)
        self.compute_body_position()

    def _substep(self, dt: float, grid: CaveGrid,
                 player_x: float, player_y: float) -> None:
        n = len(self.particles)
        fx = [0.0] * n
        fy = [0.0] * n

        # Gravity
        for i in range(n):
            fy[i] += GRAVITY

        # Chase force toward player
        dpx = player_x - self.body_x
        dpy = player_y - self.body_y
        dist_p = math.hypot(dpx, dpy)
        if 0.01 < dist_p < CHASE_RANGE:
            cax = CHASE_ACCEL * dpx / dist_p
            cay = CHASE_ACCEL * dpy / dist_p
            for i in range(n):
                fx[i] += cax
                fy[i] += cay

        # Edge springs (neighbours i ↔ i+1)
        for i in range(n):
            j = (i + 1) % n
            pi, pj = self.particles[i], self.particles[j]
            dx = pj[0] - pi[0]
            dy = pj[1] - pi[1]
            d = math.hypot(dx, dy)
            if d > 0.001:
                f = SPRING_K * (d - self._edge_rest)
                dfx = f * dx / d
                dfy = f * dy / d
                fx[i] += dfx;  fy[i] += dfy
                fx[j] -= dfx;  fy[j] -= dfy

        # Skip-1 springs (surface tension, i ↔ i+2)
        for i in range(n):
            j = (i + 2) % n
            pi, pj = self.particles[i], self.particles[j]
            dx = pj[0] - pi[0]
            dy = pj[1] - pi[1]
            d = math.hypot(dx, dy)
            if d > 0.001:
                f = SKIP_K * (d - self._skip_rest)
                dfx = f * dx / d
                dfy = f * dy / d
                fx[i] += dfx;  fy[i] += dfy
                fx[j] -= dfx;  fy[j] -= dfy

        # Pressure force (area conservation)
        area = self._polygon_area()
        vol_err = self.target_area - area
        pressure = PRESSURE_K * vol_err

        cx = sum(p[0] for p in self.particles) / n
        cy = sum(p[1] for p in self.particles) / n
        for i in range(n):
            p = self.particles[i]
            ox = p[0] - cx
            oy = p[1] - cy
            od = math.hypot(ox, oy)
            if od > 0.01:
                pf = pressure / (od * n)
                fx[i] += pf * ox
                fy[i] += pf * oy

        # Verlet integration with per-step damping
        dt2 = dt * dt
        for i in range(n):
            p = self.particles[i]
            # Damped velocity step from Verlet history
            vx = (p[0] - p[2]) * DAMPING
            vy = (p[1] - p[3]) * DAMPING
            nx = p[0] + vx + fx[i] * dt2
            ny = p[1] + vy + fy[i] * dt2
            p[2], p[3] = p[0], p[1]
            p[0], p[1] = nx, ny

        # Resolve wall penetrations
        self._resolve_collisions(grid)

    def _polygon_area(self) -> float:
        """Shoelace formula for signed area (we return magnitude)."""
        a = 0.0
        n = len(self.particles)
        for i in range(n):
            j = (i + 1) % n
            a += self.particles[i][0] * self.particles[j][1]
            a -= self.particles[j][0] * self.particles[i][1]
        return abs(a) * 0.5

    def _resolve_collisions(self, grid: CaveGrid) -> None:
        for p in self.particles:
            tx, ty = grid.world_to_tile(p[0], p[1])
            if grid.is_solid(tx, ty):
                # Revert to previous position (zeros out velocity in Verlet)
                p[0], p[1] = p[2], p[3]
                p[2], p[3] = p[0], p[1]

                # In case the old position was also somehow solid (startup),
                # snap to nearest open tile centre.
                otx, oty = grid.world_to_tile(p[0], p[1])
                if grid.is_solid(otx, oty):
                    result = grid.snap_to_open(otx, oty)
                    if result:
                        wx, wy = grid.tile_to_world(*result)
                        p[0] = wx;  p[1] = wy
                        p[2] = wx;  p[3] = wy

    # ── hit detection ─────────────────────────────────────────────────────────

    def overlaps_body(self, bx: float, by: float) -> bool:
        """True if any particle is within HIT_RADIUS of (bx, by)."""
        r2 = HIT_RADIUS * HIT_RADIUS
        for p in self.particles:
            dx = p[0] - bx
            dy = p[1] - by
            if dx * dx + dy * dy <= r2:
                return True
        return False

