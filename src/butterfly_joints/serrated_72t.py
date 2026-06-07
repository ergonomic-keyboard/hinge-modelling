"""Serrated Face Flange — 72 tooth, 90° included angle, 18mm OD.

Fine radial serrations with 5° angular resolution.
Includes cam lever clamp instead of thumb nut.
"""

from build123d import *
import math
from ..config import SerratedDims, COLORS
from ..primitives import hex_to_color, hollow_cylinder


def build_serrated_disc(dims: SerratedDims = SerratedDims(), serrations_up: bool = True) -> Part:
    """Build one serrated face disc.

    Serrations are shallow V-cuts (90° included angle, 0.5mm deep) cut into
    the face of a flat ring.
    """
    inner_r = dims.inner_bore / 2
    outer_r = dims.outer_dia / 2

    # Full disc (base + serration zone)
    disc = hollow_cylinder(outer_r, inner_r, dims.disc_thick)

    # Cut serration grooves: 72 radial V-cuts on top face
    angular_span = 360.0 / dims.tooth_count  # 5°
    half_angle = math.radians(dims.tooth_angle_deg / 2)  # 45°

    # Each serration groove is a thin wedge cut into the top face
    groove_width_at_surface = 2 * dims.serration_depth / math.tan(half_angle)

    for i in range(dims.tooth_count):
        angle = i * angular_span
        # Create a thin triangular prism as the groove
        # The groove runs radially from inner_r to outer_r
        groove_len = outer_r - inner_r + 2  # slight overcut
        with BuildPart() as gp:
            with BuildSketch(Plane.XZ):
                with BuildLine():
                    # V-groove cross section
                    hw = groove_width_at_surface / 2
                    Line((-hw, 0), (0, -dims.serration_depth))
                    Line((0, -dims.serration_depth), (hw, 0))
                    Line((hw, 0), (-hw, 0))
                make_face()
            extrude(amount=groove_len)
        groove = gp.part
        # Position radially: center the extrusion on the radial line
        mid_r = (inner_r + outer_r) / 2
        groove = Pos(0, mid_r, dims.disc_thick / 2) * groove
        groove = Rot(0, 0, angle) * groove
        disc = disc - groove

    # Central bore (clean)
    bore = Cylinder(inner_r, dims.disc_thick * 3)
    disc = disc - bore

    # Mounting ears
    for angle in [0, 180]:
        ear_x = outer_r + dims.ear_len / 2
        ear = Box(dims.ear_len, dims.ear_width, dims.ear_thick)
        ear = Pos(ear_x, 0, 0) * ear
        ear = Rot(0, 0, angle) * ear
        disc = disc + ear

        hole = Cylinder(dims.ear_hole_dia / 2, dims.ear_thick * 3)
        hole = Pos(ear_x, 0, 0) * hole
        hole = Rot(0, 0, angle) * hole
        disc = disc - hole

    if not serrations_up:
        disc = mirror(disc, about=Plane.XY)

    return disc


def build_cam_lever(dims: SerratedDims = SerratedDims()) -> Part:
    """Build quarter-turn cam lever for serrated disc clamping."""
    # Lever arm
    lever = Box(dims.cam_lever_len, dims.cam_lever_width, dims.cam_lever_thick)
    lever = Pos(dims.cam_lever_len / 2, 0, 0) * lever

    # Cam eccentric at pivot end
    cam = Cylinder(dims.cam_lever_width / 2, dims.cam_lever_thick)
    # Offset the cam center to create eccentricity
    cam = Pos(dims.cam_eccentricity, 0, 0) * cam

    lever = lever + cam

    # Pivot bore
    bore = Cylinder(CLAMP_BOLT_DIA / 2, dims.cam_lever_thick * 3)
    lever = lever - bore

    lever.label = "right_cam_lever"
    lever.color = hex_to_color(COLORS["cam_lever"])
    return lever


# Need CLAMP_BOLT_DIA for cam lever
from ..config import CLAMP_BOLT_DIA


def build_serrated_pair(dims: SerratedDims = SerratedDims()) -> list[Part]:
    """Build matched pair of serrated discs + cam lever."""
    lower = build_serrated_disc(dims, serrations_up=True)
    lower.label = "left_serrated_disc"
    lower.color = hex_to_color(COLORS["serrated_disc"])

    upper = build_serrated_disc(dims, serrations_up=False)
    upper.label = "right_serrated_disc"
    upper.color = hex_to_color(COLORS["serrated_disc"])

    cam = build_cam_lever(dims)

    return [lower, upper, cam]
