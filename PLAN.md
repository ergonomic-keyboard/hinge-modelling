# Plan: Rewrite Hinge Mechanisms in build123d

## Context

The existing hinge mechanism models are built with Three.js primitives in `wip/mechanisms/demo/index.html` (approximate shapes) and `wip/hardware-builders.js` (more accurate but still limited to boxes, cylinders, tori). The user wants precise, CAD-quality models created with [build123d](https://github.com/gumyr/build123d) that can be exported to glTF/GLB and loaded in the browser Three.js visualization.

**Why build123d?** Three.js primitives can't represent true BREP geometry — fillets, chamfers, accurate Hirth tooth profiles (varying V-groove height from bore to OD), rounded box corners, and threaded features. build123d uses the OpenCASCADE kernel for exact boundary representation and exports directly to glTF.

**Dimension source:** `wip/hardware-catalog.js` contains manufacturer-sourced dimensions (Reell PHA 8mm, 20mm Hirth disc with 24 teeth, Tekno TKR6250 turnbuckle, etc.). These supersede the demo's approximate values (60mm Hirth, 12 teeth).

## Scope

Focus on the **Turnbuckle + Hirth (Mechanism A)** assembly first, which corresponds to the **`pha-hirth` configuration** from `hinge-design.md`. This covers:
- PHA 8mm fold hinge
- Hirth 24T butterfly discs (the most geometrically complex part)
- Angled SS brackets
- M4 clamping hardware (thumb nut + Belleville washer + bolt)
- Simplified keyboard halves for context
- Turnbuckle and cables

Also model the **bearing pivot** fold hinge and **serrated 72T** butterfly joint to cover the range.

## Project Structure

```
/home/a/git/git/keyboard/hinge-modelling/
├── pyproject.toml              # build123d dependency
├── requirements.txt            # pip fallback
├── src/
│   ├── __init__.py
│   ├── config.py               # All dims ported from hardware-catalog.js
│   ├── primitives.py           # Reusable shapes (knurled cylinder, hex head, etc.)
│   ├── fold_hinges/
│   │   ├── __init__.py
│   │   ├── pha_8mm.py          # Reell PHA 8mm friction hinge
│   │   └── bearing_pivot.py    # Miniature sealed-bearing pivot
│   ├── butterfly_joints/
│   │   ├── __init__.py
│   │   ├── hirth_24t.py        # Hirth coupling with V-groove teeth
│   │   └── serrated_72t.py     # Serrated face flange
│   ├── brackets/
│   │   ├── __init__.py
│   │   └── angled_bracket.py   # 15° SS bracket pair
│   ├── clamping/
│   │   ├── __init__.py
│   │   ├── thumb_nut.py        # M4 knurled thumb nut + Belleville washer
│   │   └── clamp_bolt.py       # M4 through-bolt
│   ├── cables/
│   │   ├── __init__.py
│   │   └── turnbuckle.py       # Tekno TKR6250 M3 turnbuckle
│   ├── keyboard_half.py        # Simplified keyboard half body
│   └── assembly.py             # Compose parts into positioned assembly
├── scripts/
│   ├── build_all.py            # CLI: build all configs → output/*.glb
│   └── build_single.py         # CLI: build one config
├── output/                     # Generated GLB files (gitignored)
├── viewer/
│   └── index.html              # Minimal Three.js GLTFLoader test viewer
└── tests/
    └── test_dimensions.py      # Verify bounding boxes match catalog dims
```

## Implementation Steps

### Step 1: Project setup
- Create `pyproject.toml` with `build123d` dependency
- Create `requirements.txt` as fallback
- Install build123d: `pip install build123d`
- Verify import works: `python -c "from build123d import *; print('OK')"`
- Create directory structure and `__init__.py` files

### Step 2: `config.py` — Port dimensions from hardware-catalog.js
Port all dataclasses from `wip/hardware-catalog.js`:
- `PivotGeometry` (lines 8-16): pivot_offset=4.0, bracket_angle=15°, bracket_width=12, etc.
- `PHADims` (lines 37-50): shaft_dia=8, shaft_len=30, body 22×12×10, flag leaf 15×12×1.5
- `BearingPivotDims` (lines 62-75): pin_dia=4, pin_len=18, bearing OD=8
- `HirthDims` (lines 93-108): outer_dia=20, bore=9, 24 teeth, 60° V-groove, tooth height OD=2.3mm
- `SerratedDims` (lines 152-169): outer_dia=18, bore=9, 72 teeth, 90° angle, 0.5mm depth
- `BracketDims` (lines 186-207): arm_len≈15.5, width=12, thick=2, flange=10mm
- `TurnbuckleDims` (lines 214-226): eye-to-eye=55, body_dia=5.5, rod_dia=3
- `KeyboardHalfDims`: width=80, depth=110, thickness=4.8

### Step 3: `primitives.py` — Shared building blocks
- `hollow_cylinder(inner_r, outer_r, height)` — Cylinder - Cylinder
- `hex_prism(across_flats, height)` — RegularPolygon(6) + extrude
- `knurled_cylinder(radius, height, knurl_count, knurl_depth)` — Cylinder with PolarLocations cuts
- `belleville_washer(outer_r, inner_r, thick, cone_height)` — revolve trapezoidal profile

### Step 4: `fold_hinges/pha_8mm.py` — PHA 8mm hinge
Build using algebra mode (matches the pattern in hardware-builders.js lines 42-110):
- **Shaft**: `Cylinder(radius=4, height=30)` along Y
- **Body**: `Box(12, 22, 10)` with `fillet(edges, 1.5)` — the key improvement over Three.js
- **Flag leaf**: `Box(15, 12, 1.5)` offset from body
- **Screw holes**: 2× `Hole(1.25)` at ±4mm spacing through leaf
- **Collar grooves**: decorative `Torus(4.2, 0.3)` near shaft ends
- Label all parts and set colors for glTF export

### Step 5: `butterfly_joints/hirth_24t.py` — Hirth disc (hardest part)
The V-groove tooth profile varies in height from bore (0.7mm) to OD (2.3mm). Strategy:

1. Create base ring: `Cylinder(10, 5) - Cylinder(4.5, 5)` (OD=20mm, bore=9mm)
2. For one tooth sector (360°/24 = 15° span):
   - Define triangular cross-section at inner radius (height 0.7mm)
   - Define triangular cross-section at outer radius (height 2.3mm)
   - `loft()` between them to create radially-varying V-groove
3. Replicate with `PolarLocations(radius=0, count=24)` to create full tooth ring
4. Add 2× mounting ears with M2 holes beyond OD
5. Create matched pair: one disc teeth-up, one teeth-down (mirror Z)

Flank angle β = arcsin(tan(π/48) / tan(30°)) ≈ 13.17° — this is computed, not approximated.

### Step 6: `brackets/angled_bracket.py` — L-shaped bracket
- Flange: `Box(10, 12, 2)` lies flat on board edge
- Arm: `Box(15.5, 12, 2)` rotated 15° from horizontal
- Fillet at the bend
- 2× M2.5 holes at 8mm spacing through flange
- Build as a pair (left/right mirror)

### Step 7: `clamping/` — Thumb nut + bolt + washer
- **Thumb nut**: `Cylinder(7, 8)` (14mm OD, 8mm height) with knurled surface + M4 threaded bore
- **Belleville washer**: revolve conical annular section (M4 bore, ~9mm OD)
- **M4 bolt**: `Cylinder(2, 20)` + `hex_prism(7, 3.2)` socket head

### Step 8: `cables/turnbuckle.py` — Tekno TKR6250
- Body: `Cylinder(2.75, 20)` hexagonal (or hex prism)
- Rods: 2× `Cylinder(1.5, 17.5)` extending from body ends
- Eyes: 2× `Torus(2, 1.15)` at each end

### Step 9: `keyboard_half.py` — Simplified half
- Body: `Box(80, 110, 4.8)` in bamboo color
- Optional: 18 keycap stubs as small raised boxes

### Step 10: `assembly.py` — Compose and position
Following the stacking order from `hinge-design.md` section 4:
```
Z = 14.8mm  Thumb nut
Z = 13.0mm  Belleville washer
Z = 12.5mm  Upper Hirth disc (right bracket)
Z = 10.0mm  Teeth mesh zone
Z =  9.5mm  Lower Hirth disc (left bracket)
Z =  8.8mm  PIVOT CENTER — fold shaft here
Z =  8.0mm  PHA body
Z =  4.8mm  Board top surface
Z =  0.0mm  Table
```

Group parts for animation:
- **Center group**: PHA body, shaft, M4 bolt
- **Left group**: left bracket, lower Hirth disc, left keyboard half
- **Right group**: right bracket, upper Hirth disc, thumb nut, right keyboard half

Use build123d `Compound` with labeled children for export.

### Step 11: Export pipeline
```python
from build123d import export_gltf, Unit

export_gltf(
    to_export=assembly,
    file_path="output/pha-hirth.glb",
    binary=True,
    unit=Unit.MM,
    linear_deflection=0.01,  # 0.01mm mesh accuracy
    angular_deflection=0.1,
)
```
build123d handles Z-up→Y-up transform automatically in glTF export.

### Step 12: `viewer/index.html` — Three.js test viewer
Minimal HTML page with:
- `GLTFLoader` loading `output/pha-hirth.glb`
- Fold angle slider (0-180°) — rotates left/right groups around Y at pivot center
- Butterfly angle slider (0-45°) — rotates groups around Z
- Camera presets matching the existing demo
- Part names from build123d labels used to identify groups for animation

### Step 13: `scripts/build_all.py` — CLI entry point
```bash
python scripts/build_all.py              # builds all 6 configs
python scripts/build_single.py pha-hirth # builds one
```

### Step 14: Dimensional tests
- Verify each part's bounding box matches catalog dims (±0.1mm)
- Verify Hirth disc has exactly 24 tooth peaks (count faces)
- Verify assembly total height matches stacking order

## Key Files Referenced

| Source file | Purpose in this plan |
|---|---|
| `wip/hardware-catalog.js` | **Primary dimension source** — all dims port to `config.py` |
| `wip/hinge-design.md` | Mechanical design rationale, stacking order, tooth geometry math |
| `wip/hardware-builders.js` | Reference Three.js builders — structure mirrors this |
| `wip/mechanisms/locking_mechanism_requirements.md` | Formal requirements (REQ-MA01–MA09) |
| `wip/mechanisms/demo/index.html` | Original demo — dimensions here are SUPERSEDED by catalog |

## Verification

1. **Build verification**: `python scripts/build_all.py` completes without errors
2. **Dimension verification**: `pytest tests/test_dimensions.py` — bounding boxes match catalog
3. **Export verification**: GLB files load in Three.js viewer without errors
4. **Visual verification**: Open `viewer/index.html`, compare mechanism geometry against `wip/mechanisms/demo/index.html` side-by-side
5. **Animation verification**: Fold/butterfly sliders produce correct rotation in viewer
6. **glTF validation**: `npx gltf-validator output/pha-hirth.glb` passes
