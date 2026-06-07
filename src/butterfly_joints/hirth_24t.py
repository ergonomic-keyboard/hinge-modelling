"""Hirth Coupling — 24 tooth, 60° V-groove, 20mm OD.

The V-groove tooth height varies linearly from bore (0.7mm) to OD (2.3mm).
Flank angle beta = arcsin(tan(pi/48) / tan(30deg)) ~ 13.17 degrees.

Tooth construction: for each of 24 teeth, loft between inner triangular
cross-section and outer triangular cross-section, then union onto base ring.
"""

from build123d import *
import math
from ..config import HirthDims, COLORS
from ..primitives import hex_to_color, hollow_cylinder


def _build_single_tooth(
    inner_r: float,
    outer_r: float,
    tooth_height_id: float,
    tooth_height_od: float,
    angular_span_deg: float,
    base_z: float,
) -> Part:
    """Build one V-groove tooth spanning from inner_r to outer_r.

    The tooth is a triangular ridge centered on the X axis (angle=0),
    spanning angular_span_deg. The triangle peak points in +Z.
    """
    # Inner profile: isosceles triangle at r=inner_r
    inner_half_arc = inner_r * math.radians(angular_span_deg / 2)
    # Outer profile: isosceles triangle at r=outer_r
    outer_half_arc = outer_r * math.radians(angular_span_deg / 2)

    # Build inner cross-section on XZ plane at y=0 (we'll position at inner_r on X)
    # Actually, we'll work in cylindrical-ish coordinates.
    # Place inner profile at (inner_r, 0) and outer profile at (outer_r, 0),
    # both on the XZ plane, then loft between them.

    with BuildPart() as bp:
        # Inner face (at r = inner_r, on YZ plane)
        with BuildSketch(Plane(origin=(inner_r, 0, base_z), z_dir=(1, 0, 0))):
            with BuildLine():
                # Triangle: base on Y axis, peak at +Z (which is local +Z)
                p1 = (-inner_half_arc, 0)  # bottom-left
                p2 = (inner_half_arc, 0)   # bottom-right
                p3 = (0, tooth_height_id)  # peak
                Line(p1, p2)
                Line(p2, p3)
                Line(p3, p1)
            make_face()

        # Outer face (at r = outer_r, on YZ plane)
        with BuildSketch(Plane(origin=(outer_r, 0, base_z), z_dir=(1, 0, 0))):
            with BuildLine():
                p1 = (-outer_half_arc, 0)
                p2 = (outer_half_arc, 0)
                p3 = (0, tooth_height_od)
                Line(p1, p2)
                Line(p2, p3)
                Line(p3, p1)
            make_face()

        loft()

    return bp.part


def build_hirth_disc(dims: HirthDims = HirthDims(), teeth_up: bool = True) -> Part:
    """Build one Hirth coupling disc.

    Args:
        dims: Hirth dimensions
        teeth_up: If True, teeth face +Z (lower disc). If False, mirrored.
    """
    inner_r = dims.inner_bore / 2
    outer_r = dims.outer_dia / 2
    angular_span = 360.0 / dims.tooth_count  # 15° per tooth

    # Base ring: solid annular disc
    base_height = dims.tooth_base_thick
    base = hollow_cylinder(outer_r, inner_r, base_height)

    # Build teeth on top of base
    teeth_z = base_height / 2  # top surface of base ring

    all_teeth = None
    for i in range(dims.tooth_count):
        angle = i * angular_span
        tooth = _build_single_tooth(
            inner_r=inner_r,
            outer_r=outer_r,
            tooth_height_id=dims.tooth_height_id,
            tooth_height_od=dims.tooth_height_od,
            angular_span_deg=angular_span,
            base_z=teeth_z,
        )
        # Rotate tooth around Z axis
        tooth = Rot(0, 0, angle) * tooth
        if all_teeth is None:
            all_teeth = tooth
        else:
            all_teeth = all_teeth + tooth

    disc = base + all_teeth

    # Central bore (ensure clean through-hole)
    bore = Cylinder(inner_r, dims.disc_thick * 2)
    disc = disc - bore

    # Mounting ears at 0° and 180°
    for angle in [0, 180]:
        ear_x = outer_r + dims.ear_len / 2
        ear = Box(dims.ear_len, dims.ear_width, dims.ear_thick)
        ear = Pos(ear_x, 0, 0) * ear
        ear = Rot(0, 0, angle) * ear
        disc = disc + ear

        # Drill ear hole
        hole = Cylinder(dims.ear_hole_dia / 2, dims.ear_thick * 3)
        hole = Pos(ear_x, 0, 0) * hole
        hole = Rot(0, 0, angle) * hole
        disc = disc - hole

    if not teeth_up:
        disc = mirror(disc, about=Plane.XY)

    return disc


def build_hirth_pair(dims: HirthDims = HirthDims()) -> list[Part]:
    """Build matched pair of Hirth discs, labeled and colored."""
    lower = build_hirth_disc(dims, teeth_up=True)
    lower.label = "left_hirth_disc"
    lower.color = hex_to_color(COLORS["hirth_disc"])

    upper = build_hirth_disc(dims, teeth_up=False)
    upper.label = "right_hirth_disc"
    upper.color = hex_to_color(COLORS["hirth_disc"])

    return [lower, upper]
