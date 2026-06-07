"""Curvic Coupling — 36 tooth, arc-ground teeth, 22mm OD.

Concave teeth on one disc, convex on the other — self-centering under axial load.
Tooth profile approximated with arc segments using the grinding wheel radius.
"""

from build123d import *
import math
from ..config import CurvicDims, COLORS
from ..primitives import hex_to_color, hollow_cylinder


def _build_curvic_tooth(
    inner_r: float,
    outer_r: float,
    tooth_height_id: float,
    tooth_height_od: float,
    angular_span_deg: float,
    base_z: float,
    convex: bool = True,
) -> Part:
    """Build one curvic tooth with arc profile.

    Similar to Hirth but with rounded (arc) cross-section instead of V-groove.
    """
    inner_half_arc = inner_r * math.radians(angular_span_deg / 2)
    outer_half_arc = outer_r * math.radians(angular_span_deg / 2)

    with BuildPart() as bp:
        # Inner face
        with BuildSketch(Plane(origin=(inner_r, 0, base_z), z_dir=(1, 0, 0))):
            with BuildLine():
                Line((-inner_half_arc, 0), (inner_half_arc, 0))
                ThreePointArc((inner_half_arc, 0), (0, tooth_height_id), (-inner_half_arc, 0))
            make_face()

        # Outer face
        with BuildSketch(Plane(origin=(outer_r, 0, base_z), z_dir=(1, 0, 0))):
            with BuildLine():
                Line((-outer_half_arc, 0), (outer_half_arc, 0))
                ThreePointArc((outer_half_arc, 0), (0, tooth_height_od), (-outer_half_arc, 0))
            make_face()

        loft()

    return bp.part


def build_curvic_disc(dims: CurvicDims = CurvicDims(), convex: bool = True) -> Part:
    """Build one Curvic coupling disc.

    Args:
        dims: Curvic dimensions
        convex: True for convex teeth (disc A), False for concave (disc B)
    """
    inner_r = dims.inner_bore / 2
    outer_r = dims.outer_dia / 2
    angular_span = 360.0 / dims.tooth_count

    base_height = dims.tooth_base_thick
    base = hollow_cylinder(outer_r, inner_r, base_height)

    teeth_z = base_height / 2

    all_teeth = None
    for i in range(dims.tooth_count):
        angle = i * angular_span
        tooth = _build_curvic_tooth(
            inner_r=inner_r,
            outer_r=outer_r,
            tooth_height_id=dims.tooth_height_id,
            tooth_height_od=dims.tooth_height_od,
            angular_span_deg=angular_span,
            base_z=teeth_z,
            convex=convex,
        )
        tooth = Rot(0, 0, angle) * tooth
        if all_teeth is None:
            all_teeth = tooth
        else:
            all_teeth = all_teeth + tooth

    disc = base + all_teeth

    # Central bore
    bore = Cylinder(inner_r, dims.disc_thick * 2)
    disc = disc - bore

    # Mounting ears at 0° and 180°
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

    if not convex:
        disc = mirror(disc, about=Plane.XY)

    return disc


def build_curvic_pair(dims: CurvicDims = CurvicDims()) -> list[Part]:
    """Build matched pair of Curvic discs."""
    lower = build_curvic_disc(dims, convex=True)
    lower.label = "left_curvic_disc"
    lower.color = hex_to_color(COLORS["curvic_disc"])

    upper = build_curvic_disc(dims, convex=False)
    upper.label = "right_curvic_disc"
    upper.color = hex_to_color(COLORS["curvic_disc"])

    return [lower, upper]
