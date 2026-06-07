#!/usr/bin/env python3
"""Build a single hinge mechanism configuration → output/<name>.glb

Usage:
    python scripts/build_single.py pha-hirth
    python scripts/build_single.py bearing-curvic
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.build_all import build_config
from src.assembly import CONFIGS


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <config-name>")
        print(f"Available: {', '.join(CONFIGS.keys())}")
        return 1

    name = sys.argv[1]
    if name not in CONFIGS:
        print(f"Unknown config: {name}")
        print(f"Available: {', '.join(CONFIGS.keys())}")
        return 1

    success = build_config(name, CONFIGS[name])
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
