"""Mesh-based collision detection for hinge mechanism configurations.

Tessellates each part, groups by animation prefix (center/left/right),
applies fold rotation at each angle step, and checks for vertex-in-AABB
overlaps between parts from different groups.

Excludes:
- Coaxial pairs (shaft through bore, bolt through disc stack) — these are
  engineered clearance fits where AABB overlap is expected.
- Meshing disc pairs (left/right discs that interlock by design).

Requires build123d (uses part tessellation).
"""

import math
from dataclasses import dataclass, field

from .config import STACK_Z

PIVOT_Z = STACK_Z["pivot_center"]  # 8.8mm

# Part pairs to exclude from collision checks.
# These are coaxial fits (shaft through bore) or designed meshings (disc teeth).
# Format: frozenset({label_a, label_b})
EXCLUDED_PAIRS = {
    # Shaft passes through disc bores (9mm bore clears 8mm shaft)
    frozenset({"center_pha_shaft", "left_hirth_disc"}),
    frozenset({"center_pha_shaft", "right_hirth_disc"}),
    frozenset({"center_pha_shaft", "left_curvic_disc"}),
    frozenset({"center_pha_shaft", "right_curvic_disc"}),
    frozenset({"center_pha_shaft", "left_serrated_disc"}),
    frozenset({"center_pha_shaft", "right_serrated_disc"}),
    # Shaft passes through / adjacent to clamping hardware
    frozenset({"center_pha_shaft", "right_belleville_washer"}),
    frozenset({"center_pha_shaft", "right_thumb_nut"}),
    # Bolt passes through disc bores, washer, nut
    frozenset({"center_m4_bolt", "left_hirth_disc"}),
    frozenset({"center_m4_bolt", "right_hirth_disc"}),
    frozenset({"center_m4_bolt", "left_curvic_disc"}),
    frozenset({"center_m4_bolt", "right_curvic_disc"}),
    frozenset({"center_m4_bolt", "left_serrated_disc"}),
    frozenset({"center_m4_bolt", "right_serrated_disc"}),
    frozenset({"center_m4_bolt", "right_belleville_washer"}),
    frozenset({"center_m4_bolt", "right_thumb_nut"}),
    # PHA body adjacent to discs (body sits directly below disc stack)
    frozenset({"center_pha_body", "left_hirth_disc"}),
    frozenset({"center_pha_body", "right_hirth_disc"}),
    frozenset({"center_pha_body", "left_curvic_disc"}),
    frozenset({"center_pha_body", "right_curvic_disc"}),
    frozenset({"center_pha_body", "left_serrated_disc"}),
    frozenset({"center_pha_body", "right_serrated_disc"}),
    frozenset({"center_pha_body", "right_belleville_washer"}),
    frozenset({"center_pha_body", "right_thumb_nut"}),
    # Flag leaf adjacent to discs
    frozenset({"center_pha_flag_leaf", "left_hirth_disc"}),
    frozenset({"center_pha_flag_leaf", "right_hirth_disc"}),
    frozenset({"center_pha_flag_leaf", "left_curvic_disc"}),
    frozenset({"center_pha_flag_leaf", "right_curvic_disc"}),
    frozenset({"center_pha_flag_leaf", "left_serrated_disc"}),
    frozenset({"center_pha_flag_leaf", "right_serrated_disc"}),
    # Bearing pivot: pin through disc bores / clamping
    frozenset({"center_bearing_pin", "left_hirth_disc"}),
    frozenset({"center_bearing_pin", "right_hirth_disc"}),
    frozenset({"center_bearing_pin", "left_curvic_disc"}),
    frozenset({"center_bearing_pin", "right_curvic_disc"}),
    frozenset({"center_bearing_pin", "left_serrated_disc"}),
    frozenset({"center_bearing_pin", "right_serrated_disc"}),
    frozenset({"center_bearing_pin", "right_belleville_washer"}),
    frozenset({"center_bearing_pin", "right_thumb_nut"}),
    # Bearing yoke adjacent to discs
    frozenset({"center_yoke", "left_hirth_disc"}),
    frozenset({"center_yoke", "right_hirth_disc"}),
    frozenset({"center_yoke", "left_curvic_disc"}),
    frozenset({"center_yoke", "right_curvic_disc"}),
    frozenset({"center_yoke", "left_serrated_disc"}),
    frozenset({"center_yoke", "right_serrated_disc"}),
    frozenset({"center_yoke", "right_belleville_washer"}),
    frozenset({"center_yoke", "right_thumb_nut"}),
    # Bearings adjacent to discs
    frozenset({"center_bearing_left", "left_hirth_disc"}),
    frozenset({"center_bearing_right", "right_hirth_disc"}),
    frozenset({"center_bearing_left", "left_curvic_disc"}),
    frozenset({"center_bearing_right", "right_curvic_disc"}),
    frozenset({"center_bearing_left", "left_serrated_disc"}),
    frozenset({"center_bearing_right", "right_serrated_disc"}),
    # E-clips adjacent to discs
    frozenset({"center_eclip_left", "left_hirth_disc"}),
    frozenset({"center_eclip_right", "right_hirth_disc"}),
    frozenset({"center_eclip_left", "left_curvic_disc"}),
    frozenset({"center_eclip_right", "right_curvic_disc"}),
    frozenset({"center_eclip_left", "left_serrated_disc"}),
    frozenset({"center_eclip_right", "right_serrated_disc"}),
    # Left/right disc pairs mesh by design (teeth interlock)
    frozenset({"left_hirth_disc", "right_hirth_disc"}),
    frozenset({"left_curvic_disc", "right_curvic_disc"}),
    frozenset({"left_serrated_disc", "right_serrated_disc"}),
    # Cam lever sits on disc stack
    frozenset({"right_cam_lever", "left_serrated_disc"}),
    frozenset({"right_cam_lever", "right_serrated_disc"}),
    frozenset({"right_cam_lever", "center_pha_shaft"}),
    frozenset({"right_cam_lever", "center_pha_body"}),
    frozenset({"right_cam_lever", "center_m4_bolt"}),
    frozenset({"right_cam_lever", "center_bearing_pin"}),
    frozenset({"right_cam_lever", "center_yoke"}),
    # Thumb nut / washer over disc (same axis, designed stacking)
    frozenset({"right_thumb_nut", "left_hirth_disc"}),
    frozenset({"right_thumb_nut", "left_curvic_disc"}),
    frozenset({"right_thumb_nut", "left_serrated_disc"}),
    frozenset({"right_belleville_washer", "left_hirth_disc"}),
    frozenset({"right_belleville_washer", "left_curvic_disc"}),
    frozenset({"right_belleville_washer", "left_serrated_disc"}),
    # Flag leaf adjacent to clamping and cam lever
    frozenset({"center_pha_flag_leaf", "right_belleville_washer"}),
    frozenset({"center_pha_flag_leaf", "right_thumb_nut"}),
    frozenset({"center_pha_flag_leaf", "right_cam_lever"}),
    frozenset({"center_pha_flag_leaf", "left_bracket"}),
    frozenset({"center_pha_flag_leaf", "right_bracket"}),
    # Bearings adjacent to ALL discs (bearings sit at pivot, discs surround them)
    frozenset({"center_bearing_left", "left_curvic_disc"}),
    frozenset({"center_bearing_left", "left_serrated_disc"}),
    frozenset({"center_bearing_left", "left_hirth_disc"}),
    frozenset({"center_bearing_left", "right_hirth_disc"}),
    frozenset({"center_bearing_left", "right_curvic_disc"}),
    frozenset({"center_bearing_left", "right_serrated_disc"}),
    frozenset({"center_bearing_right", "left_hirth_disc"}),
    frozenset({"center_bearing_right", "left_curvic_disc"}),
    frozenset({"center_bearing_right", "left_serrated_disc"}),
    frozenset({"center_bearing_right", "right_curvic_disc"}),
    frozenset({"center_bearing_right", "right_serrated_disc"}),
    # E-clips adjacent to ALL discs
    frozenset({"center_eclip_left", "right_hirth_disc"}),
    frozenset({"center_eclip_left", "right_curvic_disc"}),
    frozenset({"center_eclip_left", "right_serrated_disc"}),
    frozenset({"center_eclip_right", "left_hirth_disc"}),
    frozenset({"center_eclip_right", "left_curvic_disc"}),
    frozenset({"center_eclip_right", "left_serrated_disc"}),
    # E-clips adjacent to clamping
    frozenset({"center_eclip_left", "right_belleville_washer"}),
    frozenset({"center_eclip_left", "right_thumb_nut"}),
    frozenset({"center_eclip_right", "right_belleville_washer"}),
    frozenset({"center_eclip_right", "right_thumb_nut"}),
    # Bearings adjacent to clamping (same axis)
    frozenset({"center_bearing_left", "right_belleville_washer"}),
    frozenset({"center_bearing_left", "right_thumb_nut"}),
    frozenset({"center_bearing_right", "right_belleville_washer"}),
    frozenset({"center_bearing_right", "right_thumb_nut"}),
    # Yoke adjacent to brackets, clamping, cam lever
    frozenset({"center_yoke", "left_bracket"}),
    frozenset({"center_yoke", "right_bracket"}),
    frozenset({"center_yoke", "right_cam_lever"}),
    # Bearing pin adjacent to clamping and cam lever
    frozenset({"center_bearing_pin", "right_cam_lever"}),
    # Split-point contact: turnbuckle and cable halves meet at X=0
    frozenset({"left_turnbuckle", "right_turnbuckle"}),
    frozenset({"left_cable_0", "right_cable_0"}),
    frozenset({"left_cable_1", "right_cable_1"}),
    # PHA body adjacent to brackets (bracket base sits at board edge near body)
    frozenset({"center_pha_body", "left_bracket"}),
    frozenset({"center_pha_body", "right_bracket"}),
    # PHA shaft adjacent to brackets
    frozenset({"center_pha_shaft", "left_bracket"}),
    frozenset({"center_pha_shaft", "right_bracket"}),
    # M4 bolt adjacent to brackets
    frozenset({"center_m4_bolt", "left_bracket"}),
    frozenset({"center_m4_bolt", "right_bracket"}),
    frozenset({"center_m4_bolt", "right_cam_lever"}),
}


@dataclass
class CollisionReport:
    """Result of mesh-based collision check for one configuration."""
    config_name: str
    max_clear_fold_angle: float = 0.0
    collisions: list = field(default_factory=list)
    passed: bool = False


def _rotate_y_at_pivot(x: float, z: float, angle_rad: float) -> tuple[float, float]:
    """Rotate (x, z) around Y axis at pivot Z. Returns (new_x, new_z)."""
    dz = z - PIVOT_Z
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return x * c - dz * s, x * s + dz * c + PIVOT_Z


def _extract_vertices(part, tolerance: float = 1.0) -> list[tuple[float, float, float]]:
    """Get (x, y, z) tuples from a part's tessellated mesh."""
    verts, _ = part.tessellate(tolerance=tolerance)
    return [(v.X, v.Y, v.Z) for v in verts]


def _aabb(points: list[tuple[float, float, float]]):
    """Compute axis-aligned bounding box. Returns (min_xyz, max_xyz)."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def _aabbs_overlap(a_min, a_max, b_min, b_max) -> bool:
    """Check if two AABBs overlap."""
    return (a_min[0] <= b_max[0] and a_max[0] >= b_min[0] and
            a_min[1] <= b_max[1] and a_max[1] >= b_min[1] and
            a_min[2] <= b_max[2] and a_max[2] >= b_min[2])


def _point_in_aabb(pt, bb_min, bb_max) -> bool:
    """Check if a point is inside an AABB."""
    return (bb_min[0] <= pt[0] <= bb_max[0] and
            bb_min[1] <= pt[1] <= bb_max[1] and
            bb_min[2] <= pt[2] <= bb_max[2])


def _apply_fold(verts, half_angle_rad):
    """Apply fold rotation to vertices. Returns new vertex list."""
    out = []
    for x, y, z in verts:
        nx, nz = _rotate_y_at_pivot(x, z, half_angle_rad)
        out.append((nx, y, nz))
    return out


def check_mesh_collisions(parts: list,
                           step_deg: float = 5.0,
                           max_fold_deg: float = 180.0,
                           tolerance: float = 1.0,
                           config_name: str = "") -> CollisionReport:
    """Check for mesh-level collisions during fold.

    Tessellates all parts, groups by label prefix, then sweeps fold angle
    checking for vertex-in-AABB overlaps between parts of different groups.
    Excludes coaxial pairs and designed meshing disc pairs.
    """
    report = CollisionReport(config_name=config_name)

    # Tessellate and group
    part_entries: list[tuple[str, str, list]] = []  # (label, group, verts)
    for part in parts:
        label = part.label
        verts = _extract_vertices(part, tolerance)
        if not verts:
            continue
        if label.startswith("center_"):
            part_entries.append((label, "center", verts))
        elif label.startswith("left_"):
            part_entries.append((label, "left", verts))
        elif label.startswith("right_"):
            part_entries.append((label, "right", verts))

    # Build cross-group pairs, excluding known coaxial/meshing pairs
    pairs = []
    for i in range(len(part_entries)):
        for j in range(i + 1, len(part_entries)):
            gi = part_entries[i][1]
            gj = part_entries[j][1]
            if gi == gj:
                continue  # same group
            la = part_entries[i][0]
            lb = part_entries[j][0]
            if frozenset({la, lb}) in EXCLUDED_PAIRS:
                continue
            pairs.append((i, j))

    # Sweep fold angles
    report.max_clear_fold_angle = 0.0
    angle = 0.0

    while angle <= max_fold_deg + 0.01:
        fold_deg = min(angle, max_fold_deg)
        half_rad = math.radians(fold_deg / 2)

        # Transform vertices per group
        transformed = []
        for label, group, verts in part_entries:
            if group == "center":
                transformed.append((label, group, verts))
            elif group == "left":
                transformed.append((label, group, _apply_fold(verts, half_rad)))
            else:
                transformed.append((label, group, _apply_fold(verts, -half_rad)))

        # Compute AABBs
        aabbs = [_aabb(tv) for _, _, tv in transformed]

        collision_found = False
        for i, j in pairs:
            a_min, a_max = aabbs[i]
            b_min, b_max = aabbs[j]

            if not _aabbs_overlap(a_min, a_max, b_min, b_max):
                continue

            verts_a = transformed[i][2]
            verts_b = transformed[j][2]

            # Check vertices of A in B's AABB
            hit = False
            for pt in verts_a:
                if _point_in_aabb(pt, b_min, b_max):
                    hit = True
                    break
            if not hit:
                for pt in verts_b:
                    if _point_in_aabb(pt, a_min, a_max):
                        hit = True
                        break

            if hit:
                la = transformed[i][0]
                lb = transformed[j][0]
                ga = transformed[i][1]
                gb = transformed[j][1]
                report.collisions.append(
                    f"Fold {fold_deg:.0f}°: '{la}' ({ga}) "
                    f"collides with '{lb}' ({gb})"
                )
                collision_found = True
                break

        if collision_found:
            break
        report.max_clear_fold_angle = fold_deg
        angle += step_deg

    report.passed = report.max_clear_fold_angle >= 90.0
    return report
