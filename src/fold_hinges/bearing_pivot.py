"""Miniature Sealed-Bearing Pivot — build123d model.

U-shaped yoke with two MR84ZZ bearings on a titanium pin.
Pin along Y axis.
"""

from build123d import *
from ..config import BearingPivotDims, COLORS
from ..primitives import hex_to_color, hollow_cylinder


def build_bearing_pivot(dims: BearingPivotDims = BearingPivotDims()) -> list[Part]:
    """Build bearing pivot parts, return labeled+colored list."""
    parts = []

    # ── Pivot pin along Y ──
    pin = Cylinder(
        dims.pin_dia / 2,
        dims.pin_len,
        rotation=(90, 0, 0),
    )
    pin.label = "center_bearing_pin"
    pin.color = hex_to_color(COLORS["pin"])
    parts.append(pin)

    # ── Bearings: 2× MR84ZZ, spaced along Y ──
    bearing_spacing = dims.yoke_width - dims.bearing_width
    for i, y_sign in enumerate([-1, 1]):
        y_pos = y_sign * bearing_spacing / 2
        bearing = Pos(0, y_pos, 0) * Rot(90, 0, 0) * hollow_cylinder(
            dims.bearing_od / 2, dims.bearing_id / 2, dims.bearing_width
        )
        side = "left" if i == 0 else "right"
        bearing.label = f"center_bearing_{side}"
        bearing.color = hex_to_color(COLORS["bearing"])
        parts.append(bearing)

    # ── Yoke: U-bracket ──
    # Base plate spanning between arms
    base_w = dims.yoke_width + 2 * dims.yoke_arm_width
    base = Box(dims.yoke_thick, base_w, dims.yoke_height / 2)
    base = Pos(0, 0, -dims.yoke_height / 4) * base

    # Left arm
    arm_l = Box(dims.yoke_thick, dims.yoke_arm_width, dims.yoke_height)
    arm_l = Pos(0, -(dims.yoke_width / 2 + dims.yoke_arm_width / 2), 0) * arm_l

    # Right arm
    arm_r = Box(dims.yoke_thick, dims.yoke_arm_width, dims.yoke_height)
    arm_r = Pos(0, (dims.yoke_width / 2 + dims.yoke_arm_width / 2), 0) * arm_r

    # Pre-drill pin bores in each arm before union (avoids split-solid issue)
    for arm in [arm_l, arm_r]:
        bore = Cylinder(dims.pin_dia / 2 + 0.1, dims.yoke_arm_width * 3, rotation=(90, 0, 0))
        bore = Pos(0, arm.center().Y, 0) * bore

    # Subtract bore from each arm before unioning
    bore_l = Pos(0, arm_l.center().Y, 0) * Cylinder(
        dims.pin_dia / 2 + 0.1, dims.yoke_arm_width * 3, rotation=(90, 0, 0))
    arm_l = arm_l - bore_l

    bore_r = Pos(0, arm_r.center().Y, 0) * Cylinder(
        dims.pin_dia / 2 + 0.1, dims.yoke_arm_width * 3, rotation=(90, 0, 0))
    arm_r = arm_r - bore_r

    yoke = (base + arm_l) + arm_r

    yoke.label = "center_yoke"
    yoke.color = hex_to_color(COLORS["yoke"])
    parts.append(yoke)

    # ── E-clips: thin rings at pin ends ──
    for i, y_sign in enumerate([-1, 1]):
        y_pos = y_sign * (dims.pin_len / 2 - dims.e_clip_thick / 2)
        clip = Pos(0, y_pos, 0) * Rot(90, 0, 0) * hollow_cylinder(
            dims.e_clip_dia / 2, dims.pin_dia / 2 + 0.1, dims.e_clip_thick
        )
        side = "left" if i == 0 else "right"
        clip.label = f"center_eclip_{side}"
        clip.color = hex_to_color(COLORS["e_clip"])
        parts.append(clip)

    return parts
