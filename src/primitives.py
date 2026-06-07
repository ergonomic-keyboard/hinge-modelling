"""Reusable parametric building blocks for hinge mechanism parts."""

from build123d import *
import math


def hex_to_color(hex_str: str) -> Color:
    """Convert '#RRGGBB' hex string to build123d Color."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    return Color(r, g, b)


def hollow_cylinder(outer_r: float, inner_r: float, height: float) -> Part:
    """Annular ring: outer cylinder minus inner bore."""
    return Cylinder(outer_r, height) - Cylinder(inner_r, height)


def hex_prism(across_flats: float, height: float) -> Part:
    """Regular hexagonal prism (socket head profile)."""
    # across_flats is the distance between parallel faces
    # RegularPolygon takes the circumradius (vertex radius)
    circum_r = across_flats / 2 / math.cos(math.radians(30))
    with BuildPart() as bp:
        with BuildSketch():
            RegularPolygon(circum_r, 6)
        extrude(amount=height)
    return bp.part


def knurled_cylinder(
    radius: float, height: float, knurl_count: int = 24, knurl_depth: float = 0.4
) -> Part:
    """Cylinder with diamond-knurl-like cuts around circumference."""
    base = Cylinder(radius, height)
    # Cut V-grooves around the perimeter
    groove_r = knurl_depth * 1.5  # cross-section radius of each groove
    with BuildPart() as bp:
        for i in range(knurl_count):
            angle = i * 360 / knurl_count
            x = radius * math.cos(math.radians(angle))
            y = radius * math.sin(math.radians(angle))
            with Locations([(x, y, 0)]):
                Cylinder(
                    groove_r,
                    height,
                    rotation=(0, 0, angle),
                    mode=Mode.ADD,
                )
    if bp.part is not None:
        return base - bp.part
    return base


def belleville_washer(
    outer_r: float, inner_r: float, thickness: float, cone_height: float
) -> Part:
    """Conical disc spring (Belleville washer) via revolve of trapezoidal profile."""
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                # Inner bottom edge
                p1 = (inner_r, 0)
                # Inner top edge
                p2 = (inner_r, thickness)
                # Outer top edge (raised by cone_height)
                p3 = (outer_r, cone_height + thickness)
                # Outer bottom edge (raised by cone_height)
                p4 = (outer_r, cone_height)
                Line(p1, p2)
                Line(p2, p3)
                Line(p3, p4)
                Line(p4, p1)
            make_face()
        revolve(axis=Axis.Z)
    return bp.part
