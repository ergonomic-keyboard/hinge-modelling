"""Assembly — compose and position parts into full mechanism configurations.

Following stacking order from PLAN.md:
    Z = 14.8mm  Thumb nut
    Z = 13.0mm  Belleville washer
    Z = 12.5mm  Upper Hirth disc (right bracket)
    Z = 10.0mm  Teeth mesh zone
    Z =  9.5mm  Lower Hirth disc (left bracket)
    Z =  8.8mm  PIVOT CENTER — fold shaft here
    Z =  8.0mm  PHA body
    Z =  4.8mm  Board top surface
    Z =  0.0mm  Table

Parts are labeled with center_/left_/right_ prefixes for Three.js grouping.
"""

from build123d import *
from .config import (
    STACK_Z, PHADims, BearingPivotDims, HirthDims, CurvicDims, SerratedDims,
    BracketDims, TurnbuckleDims, KeyboardHalfDims, COLORS, PIVOT_OFFSET,
)
from .primitives import hex_to_color
from .fold_hinges.pha_8mm import build_pha_8mm
from .fold_hinges.bearing_pivot import build_bearing_pivot
from .butterfly_joints.hirth_24t import build_hirth_pair
from .butterfly_joints.curvic_36t import build_curvic_pair
from .butterfly_joints.serrated_72t import build_serrated_pair
from .brackets.angled_bracket import build_bracket_pair
from .clamping.thumb_nut import build_thumb_nut, build_belleville_washer
from .clamping.clamp_bolt import build_m4_bolt
from .cables.turnbuckle import build_turnbuckle
from .cables.cable_assembly import build_cable_assembly
from .keyboard_half import build_keyboard_half


def _position_part(part: Part, z_offset: float, x_offset: float = 0, y_offset: float = 0) -> Part:
    """Move a part to a Z position (and optional XY)."""
    return Pos(x_offset, y_offset, z_offset) * part


def assemble_pha_hirth() -> list[Part]:
    """Assemble PHA 8mm + Hirth 24T configuration (Mechanism A)."""
    parts = []
    pivot_z = STACK_Z["pivot_center"]

    # ── Fold hinge: PHA 8mm ──
    pha_parts = build_pha_8mm()
    for p in pha_parts:
        p = _position_part(p, z_offset=pivot_z)
        parts.append(p)

    # ── Butterfly: Hirth 24T pair ──
    hirth_parts = build_hirth_pair()
    lower_disc = _position_part(hirth_parts[0], z_offset=STACK_Z["lower_hirth"])
    parts.append(lower_disc)
    upper_disc = _position_part(hirth_parts[1], z_offset=STACK_Z["upper_hirth"])
    parts.append(upper_disc)

    # ── Brackets ──
    bracket_parts = build_bracket_pair()
    kbd_dims = KeyboardHalfDims()
    bracket_x_offset = kbd_dims.width / 2  # inner board edge
    left_bracket = _position_part(bracket_parts[0], z_offset=STACK_Z["board_top"], x_offset=-bracket_x_offset)
    parts.append(left_bracket)
    right_bracket = _position_part(bracket_parts[1], z_offset=STACK_Z["board_top"], x_offset=bracket_x_offset)
    parts.append(right_bracket)

    # ── Clamping hardware ──
    bolt = build_m4_bolt()
    bolt = _position_part(bolt, z_offset=STACK_Z["lower_hirth"])
    parts.append(bolt)

    washer = build_belleville_washer()
    washer = _position_part(washer, z_offset=STACK_Z["belleville"])
    parts.append(washer)

    nut = build_thumb_nut()
    nut = _position_part(nut, z_offset=STACK_Z["thumb_nut"])
    parts.append(nut)

    # ── Keyboard halves ──
    left_kbd = build_keyboard_half(side="left")
    left_kbd = _position_part(left_kbd, z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                               x_offset=-(bracket_x_offset + kbd_dims.width / 2))
    parts.append(left_kbd)

    right_kbd = build_keyboard_half(side="right")
    right_kbd = _position_part(right_kbd, z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                                x_offset=(bracket_x_offset + kbd_dims.width / 2))
    parts.append(right_kbd)

    # ── Turnbuckle + cables ──
    tb_parts = build_turnbuckle()
    for tb in tb_parts:
        tb = _position_part(tb, z_offset=STACK_Z["board_top"] - 2, y_offset=60)
        parts.append(tb)

    cable_parts = build_cable_assembly(cable_length=kbd_dims.width * 2 + 40)
    for cp in cable_parts:
        cp = _position_part(cp, z_offset=STACK_Z["board_top"] - 1)
        parts.append(cp)

    return parts


def assemble_pha_curvic() -> list[Part]:
    """Assemble PHA 8mm + Curvic 36T configuration."""
    parts = []
    pivot_z = STACK_Z["pivot_center"]

    pha_parts = build_pha_8mm()
    for p in pha_parts:
        p = _position_part(p, z_offset=pivot_z)
        parts.append(p)

    curvic_parts = build_curvic_pair()
    lower_disc = _position_part(curvic_parts[0], z_offset=STACK_Z["lower_hirth"])
    parts.append(lower_disc)
    upper_disc = _position_part(curvic_parts[1], z_offset=STACK_Z["upper_hirth"])
    parts.append(upper_disc)

    bracket_parts = build_bracket_pair()
    kbd_dims = KeyboardHalfDims()
    bracket_x_offset = kbd_dims.width / 2
    left_bracket = _position_part(bracket_parts[0], z_offset=STACK_Z["board_top"], x_offset=-bracket_x_offset)
    parts.append(left_bracket)
    right_bracket = _position_part(bracket_parts[1], z_offset=STACK_Z["board_top"], x_offset=bracket_x_offset)
    parts.append(right_bracket)

    bolt = _position_part(build_m4_bolt(), z_offset=STACK_Z["lower_hirth"])
    washer = _position_part(build_belleville_washer(), z_offset=STACK_Z["belleville"])
    nut = _position_part(build_thumb_nut(), z_offset=STACK_Z["thumb_nut"])
    parts.extend([bolt, washer, nut])

    left_kbd = _position_part(build_keyboard_half(side="left"),
                               z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                               x_offset=-(bracket_x_offset + kbd_dims.width / 2))
    right_kbd = _position_part(build_keyboard_half(side="right"),
                                z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                                x_offset=(bracket_x_offset + kbd_dims.width / 2))
    parts.extend([left_kbd, right_kbd])

    return parts


def assemble_pha_serrated() -> list[Part]:
    """Assemble PHA 8mm + Serrated 72T configuration."""
    parts = []
    pivot_z = STACK_Z["pivot_center"]

    pha_parts = build_pha_8mm()
    for p in pha_parts:
        p = _position_part(p, z_offset=pivot_z)
        parts.append(p)

    serrated_parts = build_serrated_pair()
    for sp in serrated_parts:
        if "left" in sp.label:
            sp = _position_part(sp, z_offset=STACK_Z["lower_hirth"])
        elif "cam" in sp.label:
            sp = _position_part(sp, z_offset=STACK_Z["thumb_nut"])
        else:
            sp = _position_part(sp, z_offset=STACK_Z["upper_hirth"])
        parts.append(sp)

    bracket_parts = build_bracket_pair()
    kbd_dims = KeyboardHalfDims()
    bracket_x_offset = kbd_dims.width / 2
    left_bracket = _position_part(bracket_parts[0], z_offset=STACK_Z["board_top"], x_offset=-bracket_x_offset)
    right_bracket = _position_part(bracket_parts[1], z_offset=STACK_Z["board_top"], x_offset=bracket_x_offset)
    parts.extend([left_bracket, right_bracket])

    left_kbd = _position_part(build_keyboard_half(side="left"),
                               z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                               x_offset=-(bracket_x_offset + kbd_dims.width / 2))
    right_kbd = _position_part(build_keyboard_half(side="right"),
                                z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                                x_offset=(bracket_x_offset + kbd_dims.width / 2))
    parts.extend([left_kbd, right_kbd])

    return parts


def assemble_bearing_hirth() -> list[Part]:
    """Assemble Bearing Pivot + Hirth 24T configuration."""
    parts = []
    pivot_z = STACK_Z["pivot_center"]

    bearing_parts = build_bearing_pivot()
    for p in bearing_parts:
        p = _position_part(p, z_offset=pivot_z)
        parts.append(p)

    hirth_parts = build_hirth_pair()
    lower_disc = _position_part(hirth_parts[0], z_offset=STACK_Z["lower_hirth"])
    upper_disc = _position_part(hirth_parts[1], z_offset=STACK_Z["upper_hirth"])
    parts.extend([lower_disc, upper_disc])

    bracket_parts = build_bracket_pair()
    kbd_dims = KeyboardHalfDims()
    bracket_x_offset = kbd_dims.width / 2
    left_bracket = _position_part(bracket_parts[0], z_offset=STACK_Z["board_top"], x_offset=-bracket_x_offset)
    right_bracket = _position_part(bracket_parts[1], z_offset=STACK_Z["board_top"], x_offset=bracket_x_offset)
    parts.extend([left_bracket, right_bracket])

    bolt = _position_part(build_m4_bolt(), z_offset=STACK_Z["lower_hirth"])
    washer = _position_part(build_belleville_washer(), z_offset=STACK_Z["belleville"])
    nut = _position_part(build_thumb_nut(), z_offset=STACK_Z["thumb_nut"])
    parts.extend([bolt, washer, nut])

    left_kbd = _position_part(build_keyboard_half(side="left"),
                               z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                               x_offset=-(bracket_x_offset + kbd_dims.width / 2))
    right_kbd = _position_part(build_keyboard_half(side="right"),
                                z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                                x_offset=(bracket_x_offset + kbd_dims.width / 2))
    parts.extend([left_kbd, right_kbd])

    return parts


def assemble_bearing_curvic() -> list[Part]:
    """Assemble Bearing Pivot + Curvic 36T configuration."""
    parts = []
    pivot_z = STACK_Z["pivot_center"]

    bearing_parts = build_bearing_pivot()
    for p in bearing_parts:
        p = _position_part(p, z_offset=pivot_z)
        parts.append(p)

    curvic_parts = build_curvic_pair()
    lower_disc = _position_part(curvic_parts[0], z_offset=STACK_Z["lower_hirth"])
    upper_disc = _position_part(curvic_parts[1], z_offset=STACK_Z["upper_hirth"])
    parts.extend([lower_disc, upper_disc])

    bracket_parts = build_bracket_pair()
    kbd_dims = KeyboardHalfDims()
    bracket_x_offset = kbd_dims.width / 2
    left_bracket = _position_part(bracket_parts[0], z_offset=STACK_Z["board_top"], x_offset=-bracket_x_offset)
    right_bracket = _position_part(bracket_parts[1], z_offset=STACK_Z["board_top"], x_offset=bracket_x_offset)
    parts.extend([left_bracket, right_bracket])

    bolt = _position_part(build_m4_bolt(), z_offset=STACK_Z["lower_hirth"])
    washer = _position_part(build_belleville_washer(), z_offset=STACK_Z["belleville"])
    nut = _position_part(build_thumb_nut(), z_offset=STACK_Z["thumb_nut"])
    parts.extend([bolt, washer, nut])

    left_kbd = _position_part(build_keyboard_half(side="left"),
                               z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                               x_offset=-(bracket_x_offset + kbd_dims.width / 2))
    right_kbd = _position_part(build_keyboard_half(side="right"),
                                z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                                x_offset=(bracket_x_offset + kbd_dims.width / 2))
    parts.extend([left_kbd, right_kbd])

    return parts


def assemble_bearing_serrated() -> list[Part]:
    """Assemble Bearing Pivot + Serrated 72T configuration."""
    parts = []
    pivot_z = STACK_Z["pivot_center"]

    bearing_parts = build_bearing_pivot()
    for p in bearing_parts:
        p = _position_part(p, z_offset=pivot_z)
        parts.append(p)

    serrated_parts = build_serrated_pair()
    for sp in serrated_parts:
        if "left" in sp.label:
            sp = _position_part(sp, z_offset=STACK_Z["lower_hirth"])
        elif "cam" in sp.label:
            sp = _position_part(sp, z_offset=STACK_Z["thumb_nut"])
        else:
            sp = _position_part(sp, z_offset=STACK_Z["upper_hirth"])
        parts.append(sp)

    bracket_parts = build_bracket_pair()
    kbd_dims = KeyboardHalfDims()
    bracket_x_offset = kbd_dims.width / 2
    left_bracket = _position_part(bracket_parts[0], z_offset=STACK_Z["board_top"], x_offset=-bracket_x_offset)
    right_bracket = _position_part(bracket_parts[1], z_offset=STACK_Z["board_top"], x_offset=bracket_x_offset)
    parts.extend([left_bracket, right_bracket])

    left_kbd = _position_part(build_keyboard_half(side="left"),
                               z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                               x_offset=-(bracket_x_offset + kbd_dims.width / 2))
    right_kbd = _position_part(build_keyboard_half(side="right"),
                                z_offset=STACK_Z["board_top"] - kbd_dims.thickness / 2,
                                x_offset=(bracket_x_offset + kbd_dims.width / 2))
    parts.extend([left_kbd, right_kbd])

    return parts


# Registry of all 6 configurations (2 fold × 3 butterfly)
CONFIGS = {
    "pha-hirth": assemble_pha_hirth,
    "pha-curvic": assemble_pha_curvic,
    "pha-serrated": assemble_pha_serrated,
    "bearing-hirth": assemble_bearing_hirth,
    "bearing-curvic": assemble_bearing_curvic,
    "bearing-serrated": assemble_bearing_serrated,
}
