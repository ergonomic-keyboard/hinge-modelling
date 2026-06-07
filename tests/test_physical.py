"""Physical plausibility tests — pure math, no build123d dependency."""

import math
import pytest
from src.verification import (
    rotate_point_around_y_at_pivot,
    rotate_point_around_z,
    check_fold_clearance,
    check_butterfly_clearance,
    verify_config,
    PIVOT_Z,
    BRACKET_X,
    DISC_DIMS,
    CABLE_HALF_LEN,
    CABLE_Z,
    TURNBUCKLE_EYE_HALF_X,
    TURNBUCKLE_Z,
)


# ── Rotation helper tests ──

class TestRotationHelpers:
    """Test rotation math with hand-computed cases."""

    def test_fold_rotation_0_deg_identity(self):
        """0 deg rotation should return the original point."""
        x, z = rotate_point_around_y_at_pivot(40.0, 4.8, 0.0)
        assert abs(x - 40.0) < 1e-10
        assert abs(z - 4.8) < 1e-10

    def test_fold_rotation_90_deg(self):
        """90 deg rotation of point at pivot Z should only change X sign pattern.

        Point (40, 8.8) is on the pivot axis — rotating 90 deg around Y at pivot:
        - dz = 8.8 - 8.8 = 0
        - new_x = 40 * cos(90) - 0 * sin(90) = 0
        - new_z = 40 * sin(90) + 0 * cos(90) + 8.8 = 40 + 8.8 = 48.8
        """
        x, z = rotate_point_around_y_at_pivot(40.0, PIVOT_Z, math.radians(90))
        assert abs(x - 0.0) < 1e-10
        assert abs(z - 48.8) < 1e-10

    def test_fold_rotation_90_deg_board_bottom(self):
        """90 deg rotation of a point below the pivot.

        Point (40, 0) — board bottom at inner edge:
        - dz = 0 - 8.8 = -8.8
        - new_x = 40 * cos(90) - (-8.8) * sin(90) = 0 + 8.8 = 8.8
        - new_z = 40 * sin(90) + (-8.8) * cos(90) + 8.8 = 40 + 0 + 8.8 = 48.8
        """
        x, z = rotate_point_around_y_at_pivot(40.0, 0.0, math.radians(90))
        assert abs(x - 8.8) < 1e-10
        assert abs(z - 48.8) < 1e-10

    def test_fold_rotation_180_deg(self):
        """180 deg rotation should flip X sign and mirror Z around pivot.

        Point (40, 0):
        - dz = 0 - 8.8 = -8.8
        - new_x = 40 * cos(180) - (-8.8) * sin(180) = -40 - 0 = -40
        - new_z = 40 * sin(180) + (-8.8) * cos(180) + 8.8 = 0 + 8.8 + 8.8 = 17.6
        """
        x, z = rotate_point_around_y_at_pivot(40.0, 0.0, math.radians(180))
        assert abs(x - (-40.0)) < 1e-10
        assert abs(z - 17.6) < 1e-10

    def test_butterfly_rotation_0_deg_identity(self):
        """0 deg butterfly rotation should be identity."""
        x, y = rotate_point_around_z(15.0, 0.0, 0.0)
        assert abs(x - 15.0) < 1e-10
        assert abs(y - 0.0) < 1e-10

    def test_butterfly_rotation_90_deg(self):
        """90 deg rotation around Z: (15, 0) -> (0, 15)."""
        x, y = rotate_point_around_z(15.0, 0.0, math.radians(90))
        assert abs(x - 0.0) < 1e-10
        assert abs(y - 15.0) < 1e-10

    def test_butterfly_rotation_45_deg(self):
        """45 deg rotation around Z: (15, 0) -> (15*cos45, 15*sin45)."""
        x, y = rotate_point_around_z(15.0, 0.0, math.radians(45))
        expected = 15.0 * math.cos(math.radians(45))
        assert abs(x - expected) < 1e-10
        assert abs(y - expected) < 1e-10


# ── Fold clearance tests ──

class TestFoldClearance:
    """Test fold clearance across all configurations."""

    @pytest.mark.parametrize("fold_type", ["pha", "bearing"])
    @pytest.mark.parametrize("butterfly_type", ["hirth", "curvic", "serrated"])
    def test_fold_achieves_90_deg(self, fold_type, butterfly_type):
        """All 6 configs must achieve at least 90 deg fold (REQ-M03a)."""
        max_angle, collisions = check_fold_clearance(fold_type, butterfly_type)
        assert max_angle >= 90.0, (
            f"{fold_type}-{butterfly_type}: max fold = {max_angle} deg < 90 deg. "
            f"Collisions: {collisions}"
        )

    def test_pivot_offset_4mm_allows_well_beyond_90_fold(self):
        """With PIVOT_OFFSET=4mm, keyboard halves should fold well beyond 90 deg.

        At extreme fold angles (>155 deg), the board bottoms (Z=0, which is
        8.8mm below the pivot) swing past center and cross — this is physically
        correct. The design requirement is fold >= 90 deg (REQ-M03a), and 4mm
        pivot offset achieves ~155 deg, which exceeds the requirement with
        substantial margin.
        """
        max_angle, collisions = check_fold_clearance("pha", "hirth")
        assert max_angle >= 150.0, (
            f"PIVOT_OFFSET=4mm should allow >= 150 deg fold, got {max_angle} deg. "
            f"Collisions: {collisions}"
        )


# ── Butterfly clearance tests ──

class TestButterflyClearance:
    """Test butterfly clearance across all butterfly joint types."""

    @pytest.mark.parametrize("butterfly_type", ["hirth", "curvic", "serrated"])
    def test_butterfly_achieves_45_deg(self, butterfly_type):
        """All butterfly joints must achieve at least 45 deg rotation."""
        max_angle, collisions = check_butterfly_clearance(butterfly_type)
        assert max_angle >= 45.0, (
            f"{butterfly_type}: max butterfly = {max_angle} deg < 45 deg. "
            f"Collisions: {collisions}"
        )

    def test_hirth_ear_clearance_at_45_deg(self):
        """Hirth ear tips at 45 deg butterfly should be far from brackets at 40mm.

        Hirth ear tip X = OD/2 + ear_len = 10 + 5 = 15mm.
        At 22.5 deg rotation (half of 45 deg): x = 15 * cos(22.5) = 13.86mm.
        Far from bracket at 40mm.
        """
        dims = DISC_DIMS["hirth"]
        ear_tip_x = dims["outer_dia"] / 2 + dims["ear_len"]  # 15mm
        rotated_x, _ = rotate_point_around_z(ear_tip_x, 0.0, math.radians(22.5))
        assert rotated_x < BRACKET_X, (
            f"Hirth ear at 22.5 deg: x={rotated_x:.2f}mm >= bracket at {BRACKET_X}mm"
        )
        # Should have substantial margin
        assert BRACKET_X - abs(rotated_x) > 20.0, (
            f"Expected > 20mm margin, got {BRACKET_X - abs(rotated_x):.2f}mm"
        )


# ── Cable/turnbuckle fold clearance tests ──

class TestCableFoldClearance:
    """Test that split cables and turnbuckle don't collide during fold."""

    def test_pha_hirth_with_cables_achieves_90_deg(self):
        """pha-hirth (the config with cables) must still achieve 90 deg fold."""
        max_angle, collisions = check_fold_clearance("pha", "hirth", has_cables=True)
        assert max_angle >= 90.0, (
            f"pha-hirth with cables: max fold = {max_angle} deg < 90 deg. "
            f"Collisions: {collisions}"
        )

    def test_cable_outer_end_doesnt_limit_90_fold(self):
        """Cable outer end at X=100mm, Z=3.8mm should not collide at 90 deg fold.

        At 45 deg half-angle, point (100, 3.8) with pivot at Z=8.8:
        - dz = 3.8 - 8.8 = -5.0
        - right_x = 100*cos(-45) - (-5)*sin(-45) = 70.71 - 3.54 = 67.17
        - left_x = -100*cos(45) - (-5)*sin(45) = -70.71 + 3.54 = -67.17
        - left_x (-67.17) < right_x (67.17) — plenty of clearance.
        """
        half_rad = math.radians(45)
        right_x, _ = rotate_point_around_y_at_pivot(CABLE_HALF_LEN, CABLE_Z, -half_rad)
        left_x, _ = rotate_point_around_y_at_pivot(-CABLE_HALF_LEN, CABLE_Z, half_rad)
        assert left_x < right_x, (
            f"Cable ends collide at 90 deg fold: left_x={left_x:.2f} >= right_x={right_x:.2f}"
        )

    def test_turnbuckle_eye_doesnt_limit_90_fold(self):
        """Turnbuckle eye at X=27.5mm, Z=2.8mm should not collide at 90 deg fold."""
        half_rad = math.radians(45)
        right_x, _ = rotate_point_around_y_at_pivot(TURNBUCKLE_EYE_HALF_X, TURNBUCKLE_Z, -half_rad)
        left_x, _ = rotate_point_around_y_at_pivot(-TURNBUCKLE_EYE_HALF_X, TURNBUCKLE_Z, half_rad)
        assert left_x < right_x, (
            f"Turnbuckle eyes collide at 90 deg fold: left_x={left_x:.2f} >= right_x={right_x:.2f}"
        )


# ── Full config verification tests ──

class TestVerifyConfig:
    """Test the full verify_config() function for all 6 configurations."""

    ALL_CONFIGS = [
        "pha-hirth", "pha-curvic", "pha-serrated",
        "bearing-hirth", "bearing-curvic", "bearing-serrated",
    ]

    @pytest.mark.parametrize("config_name", ALL_CONFIGS)
    def test_config_passes(self, config_name):
        """All 6 configs should pass both fold and butterfly verification."""
        result = verify_config(config_name)
        assert result.passed, (
            f"{config_name}: fold={result.max_fold_angle} deg "
            f"(pass={result.fold_pass}), "
            f"butterfly={result.max_butterfly_angle} deg "
            f"(pass={result.butterfly_pass}). "
            f"Fold collisions: {result.fold_collisions}. "
            f"Butterfly collisions: {result.butterfly_collisions}"
        )

    @pytest.mark.parametrize("config_name", ALL_CONFIGS)
    def test_config_fold_at_least_90(self, config_name):
        """Verify fold_pass flag matches >= 90 deg threshold."""
        result = verify_config(config_name)
        assert result.max_fold_angle >= 90.0
        assert result.fold_pass is True

    @pytest.mark.parametrize("config_name", ALL_CONFIGS)
    def test_config_butterfly_at_least_45(self, config_name):
        """Verify butterfly_pass flag matches >= 45 deg threshold."""
        result = verify_config(config_name)
        assert result.max_butterfly_angle >= 45.0
        assert result.butterfly_pass is True
