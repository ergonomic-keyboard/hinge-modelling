"""Dimensions ported from wip/hardware-catalog.js — manufacturer-sourced values."""

from dataclasses import dataclass
import math

# ── Shared geometry constants ──
PIVOT_OFFSET = 4.0  # mm above Z_SWITCH_PLATE_TOP
BRACKET_ANGLE_DEG = 15  # degrees above horizontal
BRACKET_ARM_LEN = PIVOT_OFFSET / math.sin(math.radians(BRACKET_ANGLE_DEG))  # ~15.5mm
BRACKET_HORIZ = BRACKET_ARM_LEN * math.cos(math.radians(BRACKET_ANGLE_DEG))  # ~15.0mm
BRACKET_WIDTH = 12  # mm along Y
BRACKET_THICK = 2  # mm stainless sheet
BUTTERFLY_BORE = 9  # mm inner bore (clears 8mm shaft + gap)
CLAMP_BOLT_DIA = 4  # mm M4


@dataclass(frozen=True)
class PHADims:
    shaft_dia: float = 8
    shaft_len: float = 30
    body_len: float = 22
    body_width: float = 12
    body_height: float = 10
    body_corner_r: float = 1.5
    flag_leaf_len: float = 15
    flag_leaf_width: float = 12
    flag_leaf_thick: float = 1.5
    screw_hole_dia: float = 2.5
    screw_hole_spacing: float = 8
    torque_nm: float = 0.46
    rotation_deg: float = 360


@dataclass(frozen=True)
class BearingPivotDims:
    pin_dia: float = 4
    pin_len: float = 18
    bearing_od: float = 8
    bearing_id: float = 4
    bearing_width: float = 3
    bearing_count: int = 2
    yoke_width: float = 12
    yoke_height: float = 20
    yoke_thick: float = 2
    yoke_arm_width: float = 5
    yoke_slot_deg: float = 270
    e_clip_dia: float = 6
    e_clip_thick: float = 0.6
    rotation_deg: float = 270


@dataclass(frozen=True)
class HirthDims:
    outer_dia: float = 20
    inner_bore: float = BUTTERFLY_BORE  # 9mm
    tooth_count: int = 24
    tooth_angle_deg: float = 60
    tooth_height_od: float = 2.3
    tooth_height_id: float = 0.7
    tooth_base_thick: float = 2
    disc_thick: float = 5
    ear_len: float = 5
    ear_width: float = 6
    ear_thick: float = 2
    ear_hole_dia: float = 2


@dataclass(frozen=True)
class CurvicDims:
    outer_dia: float = 22
    inner_bore: float = BUTTERFLY_BORE
    tooth_count: int = 36
    tooth_arc_radius: float = 12
    tooth_height_od: float = 1.8
    tooth_height_id: float = 0.5
    tooth_base_thick: float = 1.5
    disc_thick: float = 4.5
    ear_len: float = 4
    ear_width: float = 6
    ear_thick: float = 2
    ear_hole_dia: float = 2


@dataclass(frozen=True)
class SerratedDims:
    outer_dia: float = 18
    inner_bore: float = BUTTERFLY_BORE
    tooth_count: int = 72
    tooth_angle_deg: float = 90
    serration_depth: float = 0.5
    tooth_base_thick: float = 2
    disc_thick: float = 2.5
    ear_len: float = 4
    ear_width: float = 5
    ear_thick: float = 1.5
    ear_hole_dia: float = 2
    cam_lever_len: float = 18
    cam_lever_width: float = 5
    cam_lever_thick: float = 2
    cam_eccentricity: float = 1.5


@dataclass(frozen=True)
class BracketDims:
    arm_len: float = BRACKET_ARM_LEN
    arm_width: float = BRACKET_WIDTH
    arm_thick: float = BRACKET_THICK
    angle_deg: float = BRACKET_ANGLE_DEG
    horizontal_reach: float = BRACKET_HORIZ
    vertical_rise: float = PIVOT_OFFSET
    mount_hole_dia: float = 2.5
    mount_hole_count: int = 2
    mount_hole_spacing: float = 8
    flange_len: float = 10
    flange_thick: float = BRACKET_THICK


@dataclass(frozen=True)
class TurnbuckleDims:
    eye_to_eye: float = 55
    body_len: float = 20
    body_dia: float = 5.5
    rod_dia: float = 3
    eye_inner: float = 1.7
    eye_outer: float = 4
    eye_thick: float = 1.5


@dataclass(frozen=True)
class EyeNutDims:
    ring_inner: float = 7.25
    ring_outer: float = 13
    ring_thick: float = 3
    nut_af: float = 5.5  # across-flats
    nut_height: float = 2.4
    total_h: float = 14
    thread_dia: float = 3
    bolt_len: float = 8


@dataclass(frozen=True)
class ClevisPinDims:
    shaft_dia: float = 5
    body_dia: float = 9
    button_dia: float = 6.5
    grip_len: float = 15
    handle_len: float = 12
    ball_dia: float = 2
    ball_count: int = 3
    total_len: float = 40


@dataclass(frozen=True)
class CableDims:
    diameter: float = 1.5


@dataclass(frozen=True)
class KeyboardHalfDims:
    width: float = 80
    depth: float = 110
    thickness: float = 4.8


@dataclass(frozen=True)
class ThumbNutDims:
    outer_dia: float = 14
    height: float = 8
    bore_dia: float = CLAMP_BOLT_DIA  # M4
    knurl_count: int = 24
    knurl_depth: float = 0.4


@dataclass(frozen=True)
class BellevilleWasherDims:
    outer_dia: float = 9
    inner_dia: float = 4.2  # M4 clearance
    thickness: float = 0.5
    cone_height: float = 0.7


@dataclass(frozen=True)
class M4BoltDims:
    shaft_dia: float = CLAMP_BOLT_DIA
    shaft_len: float = 20
    head_dia: float = 7  # socket head across-flats
    head_height: float = 3.2


# ── Color assignments for glTF export (hex strings) ──
COLORS = {
    "pha_body": "#AAAAAA",      # Chrome matte — zinc housing
    "pha_shaft": "#888888",     # Steel — polished
    "flag_leaf": "#888888",     # Steel
    "hirth_disc": "#666666",    # Dark steel — hardened tool steel
    "curvic_disc": "#666666",   # Dark steel
    "serrated_disc": "#666666", # Dark steel
    "bracket": "#BBBBBB",      # Light grey — 316L SS
    "thumb_nut": "#CC9944",    # Brass
    "belleville": "#555555",   # Dark grey — spring steel
    "m4_bolt": "#888888",      # Steel — 12.9 grade
    "turnbuckle": "#CCCCCC",   # Aluminum — anodized
    "keyboard_half": "#D4A574", # Bamboo
    "screw": "#BB7744",        # Copper tint
    "eye_nut": "#888888",      # Steel
    "clevis_pin": "#888888",   # Steel
    "cable": "#AAAAAA",        # Wire rope
    "yoke": "#BBBBBB",         # SS
    "bearing": "#888888",      # Chrome steel
    "pin": "#888888",          # Ti or SS
    "e_clip": "#555555",       # Spring steel
    "cam_lever": "#CCCCCC",    # Aluminum
}


# ── Assembly stacking order Z positions (from PLAN.md) ──
STACK_Z = {
    "table": 0.0,
    "board_top": 4.8,
    "pha_body": 8.0,
    "pivot_center": 8.8,
    "lower_hirth": 9.5,
    "teeth_mesh": 10.0,
    "upper_hirth": 12.5,
    "belleville": 13.0,
    "thumb_nut": 14.8,
}
