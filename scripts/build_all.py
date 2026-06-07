#!/usr/bin/env python3
"""Build all 6 hinge mechanism configurations → output/*.glb"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from build123d import Compound, export_gltf, Unit
from src.assembly import CONFIGS
from src.glb_postprocess import inject_labels
from src.verification import verify_config


OUTPUT_DIR = project_root / "output"


def build_config(name: str, assemble_fn, output_dir: Path = OUTPUT_DIR):
    """Build one configuration and export to GLB."""
    print(f"  Building {name}...")
    parts = assemble_fn()
    print(f"    {len(parts)} parts assembled")

    # Create Compound from all parts (preserves labels and colors)
    assembly = Compound(children=parts)

    output_dir.mkdir(parents=True, exist_ok=True)
    glb_path = output_dir / f"{name}.glb"

    success = export_gltf(
        to_export=assembly,
        file_path=str(glb_path),
        binary=True,
        unit=Unit.MM,
        linear_deflection=0.01,
        angular_deflection=0.1,
    )

    if success:
        # Post-process: inject part labels into GLB node names
        labels = [p.label for p in parts]
        inject_labels(glb_path, labels)
        size_kb = glb_path.stat().st_size / 1024
        print(f"    -> {glb_path} ({size_kb:.0f} KB)")

        # Physical plausibility verification
        result = verify_config(name)
        print(f"    Verification: fold={result.max_fold_angle:.0f}° "
              f"butterfly={result.max_butterfly_angle:.0f}°"
              f" — {'PASS' if result.passed else 'FAIL'}")
        if not result.passed:
            if result.fold_collisions:
                print(f"    Fold collisions: {result.fold_collisions[0]}")
            if result.butterfly_collisions:
                print(f"    Butterfly collisions: {result.butterfly_collisions[0]}")
            return False
    else:
        print(f"    FAILED: {glb_path}")
    return success


def main():
    configs = sys.argv[1:] if len(sys.argv) > 1 else list(CONFIGS.keys())

    print(f"Building {len(configs)} configurations:")
    results = {}
    for name in configs:
        if name not in CONFIGS:
            print(f"  Unknown config: {name}")
            print(f"  Available: {', '.join(CONFIGS.keys())}")
            results[name] = False
            continue
        try:
            results[name] = build_config(name, CONFIGS[name])
        except Exception as e:
            print(f"  ERROR building {name}: {e}")
            results[name] = False

    # Summary
    ok = sum(1 for v in results.values() if v)
    fail = len(results) - ok
    print(f"\nDone: {ok} succeeded, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
