"""M4 Knurled Thumb Nut + Belleville Washer — build123d models."""

from build123d import *
from ..config import ThumbNutDims, BellevilleWasherDims, COLORS
from ..primitives import hex_to_color, knurled_cylinder, belleville_washer as _bw_prim


def build_thumb_nut(dims: ThumbNutDims = ThumbNutDims()) -> Part:
    """Build brass knurled thumb nut with M4 through-bore."""
    nut = knurled_cylinder(
        radius=dims.outer_dia / 2,
        height=dims.height,
        knurl_count=dims.knurl_count,
        knurl_depth=dims.knurl_depth,
    )
    # M4 bore through center
    bore = Cylinder(dims.bore_dia / 2, dims.height * 2)
    nut = nut - bore

    nut.label = "right_thumb_nut"
    nut.color = hex_to_color(COLORS["thumb_nut"])
    return nut


def build_belleville_washer(dims: BellevilleWasherDims = BellevilleWasherDims()) -> Part:
    """Build Belleville (conical disc) spring washer."""
    washer = _bw_prim(
        outer_r=dims.outer_dia / 2,
        inner_r=dims.inner_dia / 2,
        thickness=dims.thickness,
        cone_height=dims.cone_height,
    )
    washer.label = "right_belleville_washer"
    washer.color = hex_to_color(COLORS["belleville"])
    return washer
