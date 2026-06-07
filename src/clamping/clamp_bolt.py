"""M4 Through-Bolt — socket head cap screw."""

from build123d import *
from ..config import M4BoltDims, COLORS
from ..primitives import hex_to_color, hex_prism


def build_m4_bolt(dims: M4BoltDims = M4BoltDims()) -> Part:
    """Build M4 socket head cap screw."""
    # Shaft
    shaft = Cylinder(dims.shaft_dia / 2, dims.shaft_len)
    shaft = Pos(0, 0, -dims.shaft_len / 2) * shaft

    # Socket head (hex prism)
    head = hex_prism(dims.head_dia, dims.head_height)
    head = Pos(0, 0, dims.head_height / 2) * head

    bolt = shaft + head

    bolt.label = "center_m4_bolt"
    bolt.color = hex_to_color(COLORS["m4_bolt"])
    return bolt
