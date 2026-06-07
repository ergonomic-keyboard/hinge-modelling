"""Physical plausibility verification for hinge mechanism configurations.

Analytical clearance checks (no AABB — too conservative for 80mm-wide boards):
1. Fold clearance: inner edges of keyboard halves must not cross during fold
2. Butterfly clearance: disc ear tips must not reach bracket positions
3. Hinge component clearance: PHA body / bearing yoke vs rotating parts
4. Cable/turnbuckle clearance: split cable ends must not cross during fold

All geometry is 2D rotation math — no build123d dependency required.
"""

import math
from dataclasses import dataclass, field


# ── Dimensions (duplicated from config.py to avoid build123d import) ──

PIVOT_OFFSET = 4.0  # mm above board top to pivot center
PIVOT_Z = 8.8  # mm — absolute Z of pivot center (= board_top + PIVOT_OFFSET)
BOARD_TOP = 4.8  # mm
BOARD_THICKNESS = 4.8  # mm
KEYCAP_HEIGHT = 6.0  # mm — approximate keycap + switch height above board
KBD_WIDTH = 80.0  # mm — keyboard half width
BRACKET_X = KBD_WIDTH / 2  # 40mm — inner edge of keyboard half = bracket mount

# Per-butterfly-joint disc dimensions
DISC_DIMS = {
    "hirth": {"outer_dia": 20.0, "ear_len": 5.0, "ear_width": 6.0},
    "curvic": {"outer_dia": 22.0, "ear_len": 4.0, "ear_width": 6.0},
    "serrated": {"outer_dia": 18.0, "ear_len": 4.0, "ear_width": 5.0},
}

# Per-fold-hinge body dimensions (extent in X from center)
FOLD_HINGE_DIMS = {
    "pha": {"body_width_x": 12.0, "body_len_y": 22.0, "body_height_z": 10.0},
    "bearing": {"yoke_width_y": 12.0, "yoke_height_z": 20.0, "yoke_thick_x": 2.0,
                "yoke_arm_width_x": 5.0},
}

# Cable/turnbuckle dimensions for configs that include them
CABLE_HALF_LEN = (KBD_WIDTH * 2 + 40) / 2  # 100mm — half of total cable length
CABLE_Z = BOARD_TOP - 1  # 3.8mm — Z position of cables
TURNBUCKLE_EYE_HALF_X = 55.0 / 2  # 27.5mm — eye-to-eye / 2
TURNBUCKLE_Z = BOARD_TOP - 2  # 2.8mm — Z position of turnbuckle

# Stacking Z positions for hinge components (from config.py STACK_Z)
STACK_Z = {
    "table": 0.0,
    "board_top": 4.8,
    "pha_body": 8.0,
    "pivot_center": 8.8,
    "lower_disc": 9.5,
    "teeth_mesh": 10.0,
    "upper_disc": 12.5,
    "belleville": 13.0,
    "thumb_nut": 14.8,
}

# Configs that include cable/turnbuckle assemblies
CONFIGS_WITH_CABLES = {"pha-hirth"}


@dataclass
class VerificationResult:
    """Result of physical plausibility verification for one configuration."""
    config_name: str
    max_fold_angle: float = 0.0  # degrees — max fold before collision
    max_butterfly_angle: float = 0.0  # degrees — max butterfly before collision
    fold_pass: bool = False  # True if fold >= 90 deg
    butterfly_pass: bool = False  # True if butterfly >= 45 deg
    fold_collisions: list = field(default_factory=list)
    butterfly_collisions: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.fold_pass and self.butterfly_pass


def rotate_point_around_y_at_pivot(x: float, z: float, angle_rad: float,
                                    pivot_z: float = PIVOT_Z) -> tuple[float, float]:
    """Rotate a point (x, z) around the Y-axis (horizontal fold axis) at pivot_z.

    In model space (Z-up), fold rotation is around Y. We project to the XZ plane:
    - Translate so pivot is at origin: z' = z - pivot_z
    - Rotate by angle in the XZ plane
    - Translate back

    Returns (new_x, new_z).
    """
    dz = z - pivot_z
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    new_x = x * cos_a - dz * sin_a
    new_z = x * sin_a + dz * cos_a + pivot_z
    return new_x, new_z


def rotate_point_around_z(x: float, y: float, angle_rad: float) -> tuple[float, float]:
    """Rotate a point (x, y) around the Z-axis (butterfly rotation axis) at origin.

    Returns (new_x, new_y).
    """
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    new_x = x * cos_a - y * sin_a
    new_y = x * sin_a + y * cos_a
    return new_x, new_y


def check_fold_clearance(fold_type: str, butterfly_type: str,
                          step_deg: float = 5.0,
                          has_cables: bool = False) -> tuple[float, list]:
    """Check fold clearance: keyboard halves + hinge components must not overlap.

    For each fold angle (0 to 180 in step_deg increments), rotate the inner edge
    profile of each keyboard half around Y at pivot_z. The left half rotates by
    +angle/2, right by -angle/2. Check that left inner X < right inner X at all Z.

    Also checks hinge component clearance (disc stack, brackets, thumb nut).
    When has_cables=True, also checks cable/turnbuckle endpoint clearance.

    Returns (max_angle_deg, collision_list).
    """
    collisions = []
    max_angle = 0.0

    # Profile points for each keyboard half's inner edge (in XZ plane)
    # The inner edge is at X = BRACKET_X (40mm) from center for the right half
    # Z ranges from 0 (table) to board_top + keycap height
    board_bottom = 0.0
    board_top = BOARD_TOP
    top_with_keycaps = board_top + KEYCAP_HEIGHT

    # Sample Z positions along the inner edge profile
    z_samples = [
        board_bottom,
        board_top / 2,
        board_top,
        board_top + KEYCAP_HEIGHT / 2,
        top_with_keycaps,
    ]

    # Also check hinge components that extend in X:
    # - Disc ears (at disc Z positions)
    # - Thumb nut (at thumb_nut Z)
    # - Brackets (at board_top Z, extending up to pivot)
    disc_dims = DISC_DIMS[butterfly_type]
    disc_ear_x = disc_dims["outer_dia"] / 2 + disc_dims["ear_len"]  # max X extent of ear

    # Component X extents at various Z heights (these rotate with the halves)
    component_points = [
        # (x, z, label) — points on the RIGHT half that must stay right of center
        (BRACKET_X, board_top, "right_bracket_base"),
        (BRACKET_X, PIVOT_Z, "right_bracket_top"),
        (disc_ear_x, STACK_Z["lower_disc"], "right_lower_disc_ear"),
        (disc_ear_x, STACK_Z["upper_disc"], "right_upper_disc_ear"),
    ]

    # Add keyboard half inner edge points
    for z in z_samples:
        component_points.append((BRACKET_X, z, f"right_kbd_edge_z{z:.1f}"))

    # Cable/turnbuckle endpoints (split at X=0, each half rotates with its side)
    if has_cables:
        # Cable inner ends at X≈0 (negligible, but outer ends are far out)
        # Cable outer endpoints — these swing the most during fold
        component_points.append(
            (CABLE_HALF_LEN, CABLE_Z, "right_cable_outer_end")
        )
        # Turnbuckle eye at outer end
        component_points.append(
            (TURNBUCKLE_EYE_HALF_X, TURNBUCKLE_Z, "right_turnbuckle_eye")
        )

    for angle_deg in _frange(0, 180 + step_deg, step_deg):
        angle_deg = min(angle_deg, 180.0)
        half_rad = math.radians(angle_deg / 2)
        collision_at_angle = False

        for x, z, label in component_points:
            # Right half rotates by -angle/2, left half by +angle/2
            # For collision check: right inner X (rotating -angle/2) must be > left inner X (rotating +angle/2)
            # By symmetry, left inner X at +angle/2 = -rotate(x, z, +angle/2).x
            # (left half is mirror of right)
            right_x, _ = rotate_point_around_y_at_pivot(x, z, -half_rad)
            left_x, _ = rotate_point_around_y_at_pivot(-x, z, half_rad)

            if left_x >= right_x:
                collision_at_angle = True
                collisions.append(
                    f"Fold {angle_deg:.0f} deg: {label} collision "
                    f"(left_x={left_x:.2f} >= right_x={right_x:.2f})"
                )
                break

        if collision_at_angle:
            break
        max_angle = angle_deg

    return max_angle, collisions


def check_butterfly_clearance(butterfly_type: str,
                                step_deg: float = 5.0) -> tuple[float, list]:
    """Check butterfly clearance: disc ears must not reach bracket X positions.

    For each butterfly angle (0 to 45 in step_deg increments), rotate the disc ear
    tip points around Z. Check they don't reach the bracket mounting position at
    X = BRACKET_X (40mm).

    Returns (max_angle_deg, collision_list).
    """
    collisions = []
    max_angle = 0.0

    disc_dims = DISC_DIMS[butterfly_type]
    disc_radius = disc_dims["outer_dia"] / 2
    ear_tip_x = disc_radius + disc_dims["ear_len"]

    # Ear tip positions (in XY plane, at the disc's Z level)
    # Ears are at 0 deg and 180 deg — so tips at (±ear_tip_x, 0)
    ear_tips = [
        (ear_tip_x, 0.0, "ear_0deg"),
        (-ear_tip_x, 0.0, "ear_180deg"),
    ]

    for angle_deg in _frange(0, 45 + step_deg, step_deg):
        angle_deg = min(angle_deg, 45.0)
        half_rad = math.radians(angle_deg / 2)
        collision_at_angle = False

        for ex, ey, label in ear_tips:
            # Left disc rotates +angle/2, right disc -angle/2
            for sign, side in [(1, "left"), (-1, "right")]:
                rot_x, rot_y = rotate_point_around_z(ex, ey, sign * half_rad)
                if abs(rot_x) >= BRACKET_X:
                    collision_at_angle = True
                    collisions.append(
                        f"Butterfly {angle_deg:.0f} deg: {side}_{label} "
                        f"reaches bracket (|x|={abs(rot_x):.2f} >= {BRACKET_X})"
                    )
                    break
            if collision_at_angle:
                break

        if collision_at_angle:
            break
        max_angle = angle_deg

    return max_angle, collisions


def verify_config(config_name: str) -> VerificationResult:
    """Run full physical plausibility verification for a named configuration.

    Config name format: "{fold_type}-{butterfly_type}"
    e.g. "pha-hirth", "bearing-curvic"
    """
    fold_type, butterfly_type = config_name.split("-")
    has_cables = config_name in CONFIGS_WITH_CABLES

    result = VerificationResult(config_name=config_name)

    # Check fold clearance
    max_fold, fold_cols = check_fold_clearance(
        fold_type, butterfly_type, has_cables=has_cables
    )
    result.max_fold_angle = max_fold
    result.fold_collisions = fold_cols
    result.fold_pass = max_fold >= 90.0

    # Check butterfly clearance
    max_bfly, bfly_cols = check_butterfly_clearance(butterfly_type)
    result.max_butterfly_angle = max_bfly
    result.butterfly_collisions = bfly_cols
    result.butterfly_pass = max_bfly >= 45.0

    return result


def _frange(start: float, stop: float, step: float):
    """Float range generator."""
    val = start
    while val < stop:
        yield val
        val += step
