"""Tekno TKR6250 M3 Turnbuckle — aluminum body with threaded rod ends.

Split into left/right halves so each side rotates with its keyboard half
during fold animation.
"""

from build123d import *
from ..config import TurnbuckleDims, COLORS
from ..primitives import hex_to_color, hex_prism


def build_turnbuckle(dims: TurnbuckleDims = TurnbuckleDims()) -> list[Part]:
    """Build turnbuckle as two halves (left + right) split at X=0.

    Returns [left_turnbuckle, right_turnbuckle].
    """
    rod_len = (dims.eye_to_eye - dims.body_len) / 2  # ~17.5mm each side
    half_body_len = dims.body_len / 2  # 10mm each side

    eye_center_r = (dims.eye_outer + dims.eye_inner) / 2 / 2
    eye_tube_r = (dims.eye_outer - dims.eye_inner) / 2 / 2

    color = hex_to_color(COLORS["turnbuckle"])

    # ── Left half (negative X) ──
    body_l = hex_prism(dims.body_dia, half_body_len)
    body_l = Rot(0, 90, 0) * body_l
    body_l = Pos(-half_body_len / 2, 0, 0) * body_l

    rod_l = Cylinder(dims.rod_dia / 2, rod_len, rotation=(0, 90, 0))
    rod_l = Pos(-(half_body_len + rod_len / 2), 0, 0) * rod_l

    eye_l = Torus(eye_center_r, eye_tube_r)
    eye_l = Rot(0, 90, 0) * eye_l
    eye_l = Pos(-(dims.eye_to_eye / 2), 0, 0) * eye_l

    left = body_l + rod_l + eye_l
    left.label = "left_turnbuckle"
    left.color = color

    # ── Right half (positive X) ──
    body_r = hex_prism(dims.body_dia, half_body_len)
    body_r = Rot(0, 90, 0) * body_r
    body_r = Pos(half_body_len / 2, 0, 0) * body_r

    rod_r = Cylinder(dims.rod_dia / 2, rod_len, rotation=(0, 90, 0))
    rod_r = Pos((half_body_len + rod_len / 2), 0, 0) * rod_r

    eye_r = Torus(eye_center_r, eye_tube_r)
    eye_r = Rot(0, 90, 0) * eye_r
    eye_r = Pos((dims.eye_to_eye / 2), 0, 0) * eye_r

    right = body_r + rod_r + eye_r
    right.label = "right_turnbuckle"
    right.color = color

    return [left, right]
