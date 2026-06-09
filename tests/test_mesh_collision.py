"""Mesh-based collision tests — requires build123d (builds actual assemblies)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.assembly import CONFIGS
from src.mesh_collision import check_mesh_collisions


ALL_CONFIGS = list(CONFIGS.keys())


class TestMeshCollision:
    """Test that all 6 configs pass mesh-based collision detection."""

    @pytest.mark.parametrize("config_name", ALL_CONFIGS)
    def test_config_clears_90_degrees(self, config_name):
        """Every config must fold to at least 90° without mesh collisions."""
        parts = CONFIGS[config_name]()
        report = check_mesh_collisions(
            parts, step_deg=5.0, tolerance=1.0, config_name=config_name
        )
        assert report.passed, (
            f"{config_name}: mesh collision at {report.max_clear_fold_angle}° "
            f"(need >= 90°). Collisions: {report.collisions}"
        )

    @pytest.mark.parametrize("config_name", ALL_CONFIGS)
    def test_config_clears_well_past_90(self, config_name):
        """All configs should clear well past 90° — expect at least 120°."""
        parts = CONFIGS[config_name]()
        report = check_mesh_collisions(
            parts, step_deg=5.0, tolerance=1.0, config_name=config_name
        )
        assert report.max_clear_fold_angle >= 120.0, (
            f"{config_name}: only clears to {report.max_clear_fold_angle}° "
            f"(expected >= 120°). Collisions: {report.collisions}"
        )

    def test_first_collision_is_brackets(self):
        """The first collision should be left/right brackets at extreme fold."""
        parts = CONFIGS["pha-hirth"]()
        report = check_mesh_collisions(
            parts, step_deg=5.0, tolerance=1.0, config_name="pha-hirth"
        )
        assert len(report.collisions) > 0, "Expected at least one collision at extreme fold"
        assert "bracket" in report.collisions[0], (
            f"Expected bracket collision, got: {report.collisions[0]}"
        )
