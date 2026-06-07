"""Wire rope + eye nuts + clevis pins — cable tensioning assembly.

Cables are split into left/right halves at X=0 so each side rotates with
its keyboard half during fold animation. Eye nuts and clevis pins are
positioned at the cable endpoints on their respective sides.
"""

from build123d import *
from ..config import CableDims, EyeNutDims, ClevisPinDims, COLORS
from ..primitives import hex_to_color, hex_prism


def build_eye_nut(dims: EyeNutDims = EyeNutDims()) -> Part:
    """Build M3 304SS lifting eye nut: ring + hex base + threaded stud."""
    ring_center_r = (dims.ring_outer + dims.ring_inner) / 2 / 2
    ring_tube_r = (dims.ring_outer - dims.ring_inner) / 2 / 2
    ring = Torus(ring_center_r, ring_tube_r)
    ring = Pos(0, 0, dims.nut_height + ring_center_r) * ring

    nut = hex_prism(dims.nut_af, dims.nut_height)
    nut = Pos(0, 0, dims.nut_height / 2) * nut

    stud = Cylinder(dims.thread_dia / 2, dims.bolt_len)
    stud = Pos(0, 0, -dims.bolt_len / 2) * stud

    eye_nut = ring + nut + stud
    return eye_nut


def build_clevis_pin(dims: ClevisPinDims = ClevisPinDims()) -> Part:
    """Build 5mm ball-lock quick-release pin."""
    shaft = Cylinder(dims.shaft_dia / 2, dims.grip_len)
    body = Cylinder(dims.body_dia / 2, dims.handle_len)
    body = Pos(0, 0, dims.grip_len / 2 + dims.handle_len / 2) * body
    button = Cylinder(dims.button_dia / 2, 3)
    button = Pos(0, 0, dims.grip_len / 2 + dims.handle_len + 1.5) * button
    pin = shaft + body + button
    return pin


def build_cable_assembly(cable_length: float = 150) -> list[Part]:
    """Build cable assembly with left/right split cables and positioned hardware.

    Each cable is split at X=0 into left and right halves. Eye nuts are placed
    at the outer ends of each cable. Clevis pins are placed at the outer ends,
    oriented vertically (along Z) to pin through the eye nut ring into the board.

    Layout per cable (2 cables at Y=±20mm):
        left eye nut --- left cable --- | X=0 | --- right cable --- right eye nut
        left clevis pin                                          right clevis pin
    """
    parts = []
    cable_dims = CableDims()
    eye_dims = EyeNutDims()
    pin_dims = ClevisPinDims()

    half_len = cable_length / 2

    # 2 cables at Y = -20mm and Y = +20mm
    y_offsets = [-20, 20]

    for i, y_off in enumerate(y_offsets):
        # ── Left half-cable ──
        cable_l = Cylinder(cable_dims.diameter / 2, half_len, rotation=(0, 90, 0))
        cable_l = Pos(-half_len / 2, y_off, 0) * cable_l
        cable_l.label = f"left_cable_{i}"
        cable_l.color = hex_to_color(COLORS["cable"])
        parts.append(cable_l)

        # ── Right half-cable ──
        cable_r = Cylinder(cable_dims.diameter / 2, half_len, rotation=(0, 90, 0))
        cable_r = Pos(half_len / 2, y_off, 0) * cable_r
        cable_r.label = f"right_cable_{i}"
        cable_r.color = hex_to_color(COLORS["cable"])
        parts.append(cable_r)

        # ── Eye nuts at outer ends ──
        nut_l = build_eye_nut(eye_dims)
        nut_l = Pos(-half_len, y_off, 0) * nut_l
        nut_l.label = f"left_eye_nut_{i}"
        nut_l.color = hex_to_color(COLORS["eye_nut"])
        parts.append(nut_l)

        nut_r = build_eye_nut(eye_dims)
        nut_r = Pos(half_len, y_off, 0) * nut_r
        nut_r.label = f"right_eye_nut_{i}"
        nut_r.color = hex_to_color(COLORS["eye_nut"])
        parts.append(nut_r)

        # ── Clevis pins at outer ends (vertical, along Z) ──
        pin_l = build_clevis_pin(pin_dims)
        pin_l = Pos(-half_len, y_off, 0) * pin_l
        pin_l.label = f"left_clevis_pin_{i}"
        pin_l.color = hex_to_color(COLORS["clevis_pin"])
        parts.append(pin_l)

        pin_r = build_clevis_pin(pin_dims)
        pin_r = Pos(half_len, y_off, 0) * pin_r
        pin_r.label = f"right_clevis_pin_{i}"
        pin_r.color = hex_to_color(COLORS["clevis_pin"])
        parts.append(pin_r)

    return parts
