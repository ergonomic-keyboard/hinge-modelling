"""Simplified keyboard half body — bamboo-colored box with optional keycap stubs."""

from build123d import *
from .config import KeyboardHalfDims, COLORS
from .primitives import hex_to_color


def build_keyboard_half(dims: KeyboardHalfDims = KeyboardHalfDims(), side: str = "left") -> Part:
    """Build simplified keyboard half body.

    Args:
        dims: Keyboard half dimensions
        side: 'left' or 'right' — affects label prefix
    """
    body = Box(dims.width, dims.depth, dims.thickness)

    # Optional keycap stubs: 3 rows × 4 cols grid (fits within 80mm width)
    key_w, key_d, key_h = 14, 14, 2
    key_spacing = 19  # standard 1U spacing
    cols, rows = 4, 3
    start_x = -(cols - 1) * key_spacing / 2
    start_y = -(rows - 1) * key_spacing / 2

    for row in range(rows):
        for col in range(cols):
            kx = start_x + col * key_spacing
            ky = start_y + row * key_spacing
            kz = dims.thickness / 2 + key_h / 2
            key = Box(key_w, key_d, key_h)
            key = Pos(kx, ky, kz) * key
            body = body + key

    body.label = f"{side}_keyboard_half"
    body.color = hex_to_color(COLORS["keyboard_half"])
    return body
