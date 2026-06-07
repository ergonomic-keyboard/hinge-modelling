"""Angled L-bracket pair — 15° SS bracket connecting board edge to pivot center."""

from build123d import *
import math
from ..config import BracketDims, COLORS
from ..primitives import hex_to_color


def build_bracket(dims: BracketDims = BracketDims()) -> Part:
    """Build one angled bracket (left side).

    Flange sits flat on board edge (XY plane).
    Arm rises at bracket_angle from horizontal toward pivot center.
    """
    # Flange: flat on the board edge
    flange = Box(dims.flange_len, dims.arm_width, dims.flange_thick)
    flange = Pos(-dims.flange_len / 2, 0, dims.flange_thick / 2) * flange

    # Arm: angled upward from the board edge
    arm = Box(dims.arm_len, dims.arm_width, dims.arm_thick)
    # Rotate arm by angle_deg about Y, pivot at the bend point
    arm = Pos(dims.arm_len / 2, 0, dims.arm_thick / 2) * arm
    arm = Rot(0, dims.angle_deg, 0) * arm

    bracket = flange + arm

    # Fillet the bend edges where flange meets arm
    # (skip if fillet fails due to topology — just leave sharp)
    try:
        bend_edges = bracket.edges().filter_by(Axis.Y).sort_by(Axis.Z)[1:3]
        if len(bend_edges) > 0:
            bracket = fillet(bend_edges, dims.arm_thick * 0.4)
    except Exception:
        pass

    # Drill mounting holes through flange
    for i in range(dims.mount_hole_count):
        y_off = (i - (dims.mount_hole_count - 1) / 2) * dims.mount_hole_spacing
        hole = Cylinder(dims.mount_hole_dia / 2, dims.flange_thick * 3)
        hole = Pos(-dims.flange_len / 2, y_off, dims.flange_thick / 2) * hole
        bracket = bracket - hole

    return bracket


def build_bracket_pair(dims: BracketDims = BracketDims()) -> list[Part]:
    """Build left and right bracket (right is mirrored)."""
    left = build_bracket(dims)
    left.label = "left_bracket"
    left.color = hex_to_color(COLORS["bracket"])

    right = mirror(build_bracket(dims), about=Plane.YZ)
    right.label = "right_bracket"
    right.color = hex_to_color(COLORS["bracket"])

    return [left, right]
