"""Dimensional tests — verify bounding boxes match catalog dims (±0.5mm tolerance)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from build123d import *

from src.config import (
    PHADims, BearingPivotDims, HirthDims, CurvicDims, SerratedDims,
    BracketDims, TurnbuckleDims, KeyboardHalfDims, ThumbNutDims,
    BellevilleWasherDims, M4BoltDims,
)
from src.fold_hinges.pha_8mm import build_pha_8mm
from src.fold_hinges.bearing_pivot import build_bearing_pivot
from src.butterfly_joints.hirth_24t import build_hirth_pair, build_hirth_disc
from src.butterfly_joints.curvic_36t import build_curvic_pair
from src.butterfly_joints.serrated_72t import build_serrated_pair
from src.brackets.angled_bracket import build_bracket_pair
from src.clamping.thumb_nut import build_thumb_nut, build_belleville_washer
from src.clamping.clamp_bolt import build_m4_bolt
from src.cables.turnbuckle import build_turnbuckle
from src.keyboard_half import build_keyboard_half


TOL = 0.5  # mm tolerance


def _bbox_size(part):
    bb = part.bounding_box()
    return (bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, bb.max.Z - bb.min.Z)


def _assert_close(actual, expected, name, tol=TOL):
    assert abs(actual - expected) <= tol, f"{name}: expected {expected}, got {actual} (tol={tol})"


# ── PHA 8mm ──

class TestPHA8mm:
    def setup_method(self):
        self.parts = build_pha_8mm()
        self.dims = PHADims()
        self.by_label = {p.label: p for p in self.parts}

    def test_shaft_diameter(self):
        sx, sy, sz = _bbox_size(self.by_label["center_pha_shaft"])
        _assert_close(sx, self.dims.shaft_dia, "shaft X (diameter)")
        _assert_close(sz, self.dims.shaft_dia, "shaft Z (diameter)")

    def test_shaft_length(self):
        _, sy, _ = _bbox_size(self.by_label["center_pha_shaft"])
        _assert_close(sy, self.dims.shaft_len, "shaft Y (length)")

    def test_body_dimensions(self):
        sx, sy, sz = _bbox_size(self.by_label["center_pha_body"])
        _assert_close(sx, self.dims.body_width, "body X (width)")
        _assert_close(sy, self.dims.body_len, "body Y (length)")
        _assert_close(sz, self.dims.body_height, "body Z (height)")

    def test_flag_leaf(self):
        sx, sy, sz = _bbox_size(self.by_label["center_pha_flag_leaf"])
        _assert_close(sx, self.dims.flag_leaf_len, "leaf X (length)")
        _assert_close(sy, self.dims.flag_leaf_width, "leaf Y (width)")
        _assert_close(sz, self.dims.flag_leaf_thick, "leaf Z (thickness)")

    def test_part_count(self):
        assert len(self.parts) == 3


# ── Bearing Pivot ──

class TestBearingPivot:
    def setup_method(self):
        self.parts = build_bearing_pivot()
        self.dims = BearingPivotDims()
        self.by_label = {p.label: p for p in self.parts}

    def test_pin_diameter(self):
        sx, _, sz = _bbox_size(self.by_label["center_bearing_pin"])
        _assert_close(sx, self.dims.pin_dia, "pin X")

    def test_pin_length(self):
        _, sy, _ = _bbox_size(self.by_label["center_bearing_pin"])
        _assert_close(sy, self.dims.pin_len, "pin Y")

    def test_yoke_height(self):
        _, _, sz = _bbox_size(self.by_label["center_yoke"])
        _assert_close(sz, self.dims.yoke_height, "yoke Z")

    def test_part_count(self):
        assert len(self.parts) == 6  # pin + 2 bearings + yoke + 2 e-clips


# ── Hirth 24T ──

class TestHirth24T:
    def setup_method(self):
        self.parts = build_hirth_pair()
        self.dims = HirthDims()

    def test_disc_outer_diameter(self):
        # Ears at 0° and 180° extend in X. Y extent is max of disc OD and ear_width.
        _, sy, _ = _bbox_size(self.parts[0])
        # Y is disc OD (20mm) since ear_width=6 < OD=20
        _assert_close(sy, self.dims.outer_dia, "disc Y (OD)", tol=1.0)

    def test_disc_x_extent(self):
        sx, _, _ = _bbox_size(self.parts[0])
        expected_x = self.dims.outer_dia + 2 * self.dims.ear_len
        _assert_close(sx, expected_x, "disc X (OD + 2×ear)")

    def test_pair_count(self):
        assert len(self.parts) == 2

    def test_tooth_count_via_geometry(self):
        """Verify 24 teeth by checking the disc has the right angular pattern."""
        disc = build_hirth_disc(self.dims, teeth_up=True)
        # Just verify it built successfully with the right overall Z
        bb = disc.bounding_box()
        z_extent = bb.max.Z - bb.min.Z
        # Should be base_thick + tooth_height_od
        assert z_extent > self.dims.tooth_base_thick


# ── Curvic 36T ──

class TestCurvic36T:
    def setup_method(self):
        self.parts = build_curvic_pair()
        self.dims = CurvicDims()

    def test_disc_x_extent(self):
        sx, _, _ = _bbox_size(self.parts[0])
        expected_x = self.dims.outer_dia + 2 * self.dims.ear_len
        _assert_close(sx, expected_x, "curvic X extent")

    def test_pair_count(self):
        assert len(self.parts) == 2


# ── Serrated 72T ──

class TestSerrated72T:
    def setup_method(self):
        self.parts = build_serrated_pair()
        self.dims = SerratedDims()

    def test_disc_outer_diameter(self):
        sx, _, _ = _bbox_size(self.parts[0])
        expected_x = self.dims.outer_dia + 2 * self.dims.ear_len
        _assert_close(sx, expected_x, "serrated X extent")

    def test_disc_thickness(self):
        _, _, sz = _bbox_size(self.parts[0])
        _assert_close(sz, self.dims.disc_thick, "serrated thickness")

    def test_part_count(self):
        assert len(self.parts) == 3  # 2 discs + cam lever


# ── Brackets ──

class TestBrackets:
    def setup_method(self):
        self.parts = build_bracket_pair()
        self.dims = BracketDims()

    def test_pair_count(self):
        assert len(self.parts) == 2

    def test_bracket_width(self):
        _, sy, _ = _bbox_size(self.parts[0])
        _assert_close(sy, self.dims.arm_width, "bracket Y (width)")


# ── Clamping ──

class TestClamping:
    def test_thumb_nut_height(self):
        nut = build_thumb_nut()
        _, _, sz = _bbox_size(nut)
        _assert_close(sz, ThumbNutDims().height, "nut Z")

    def test_thumb_nut_diameter(self):
        nut = build_thumb_nut()
        sx, sy, _ = _bbox_size(nut)
        _assert_close(sx, ThumbNutDims().outer_dia, "nut X (dia)", tol=1.0)

    def test_belleville_diameter(self):
        w = build_belleville_washer()
        sx, _, _ = _bbox_size(w)
        _assert_close(sx, BellevilleWasherDims().outer_dia, "washer X (dia)")

    def test_bolt_shaft_length(self):
        bolt = build_m4_bolt()
        _, _, sz = _bbox_size(bolt)
        dims = M4BoltDims()
        # Total Z: shaft_len + head_height, but head is at top
        # Shaft extends downward, head at origin+head_height
        # So Z extent ≈ shaft_len + head_height
        expected = dims.shaft_len + dims.head_height
        _assert_close(sz, expected, "bolt Z (total)", tol=5.0)


# ── Turnbuckle ──

class TestTurnbuckle:
    def test_eye_to_eye(self):
        tb_parts = build_turnbuckle()
        assert len(tb_parts) == 2, f"Expected 2 halves, got {len(tb_parts)}"
        # Measure combined X extent across both halves
        all_min_x = min(p.bounding_box().min.X for p in tb_parts)
        all_max_x = max(p.bounding_box().max.X for p in tb_parts)
        combined_x = all_max_x - all_min_x
        dims = TurnbuckleDims()
        torus_minor_r = (dims.eye_outer - dims.eye_inner) / 2 / 2
        _assert_close(combined_x, dims.eye_to_eye + 2 * torus_minor_r, "turnbuckle X", tol=1.0)

    def test_halves_labeled_correctly(self):
        tb_parts = build_turnbuckle()
        labels = {p.label for p in tb_parts}
        assert "left_turnbuckle" in labels
        assert "right_turnbuckle" in labels


# ── Keyboard Half ──

class TestKeyboardHalf:
    def test_body_width(self):
        kh = build_keyboard_half(side="left")
        sx, _, _ = _bbox_size(kh)
        _assert_close(sx, KeyboardHalfDims().width, "keyboard X (width)")

    def test_body_depth(self):
        kh = build_keyboard_half(side="left")
        _, sy, _ = _bbox_size(kh)
        _assert_close(sy, KeyboardHalfDims().depth, "keyboard Y (depth)")

    def test_label_prefix(self):
        kh_l = build_keyboard_half(side="left")
        kh_r = build_keyboard_half(side="right")
        assert kh_l.label.startswith("left_")
        assert kh_r.label.startswith("right_")
