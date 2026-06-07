# Session Handover — Hinge Modelling

## What this repo is

Precise 3D hinge mechanism models built with **build123d** (Python CAD library), exported to **GLB** for import into a Three.js keyboard visualization. The repo lives at `/home/a/git/git/keyboard/hinge-modelling/`. Dimensions come from `/home/a/git/git/keyboard/wip/hardware-catalog.js` (read-only — do not modify anything in `wip/`).

The project models a **split keyboard hinge system**: 2 fold hinge types × 3 butterfly joint types = **6 configurations**.

## What has been completed (Steps 1–16)

All 16 steps from `PLAN.md` are done and working:

1. **Project setup** — Python 3.12 venv at `.venv`, build123d installed
2. **config.py** — All dimensions ported as frozen dataclasses from `hardware-catalog.js`
3. **primitives.py** — `hex_to_color()`, `hollow_cylinder()`, `hex_prism()`, `knurled_cylinder()`, `belleville_washer()`
4. **pha_8mm.py** — Reell PHA 8mm friction hinge (shaft + body + flag leaf)
5. **hirth_24t.py** — 24-tooth Hirth coupling with lofted V-groove teeth (most complex part)
6. **curvic_36t.py** — 36-tooth curvic coupling with arc-ground teeth
7. **serrated_72t.py** — 72-tooth serrated face flange + cam lever
8. **angled_bracket.py** — 15° L-bracket pair (left/right mirror)
9. **thumb_nut.py + clamp_bolt.py** — M4 knurled nut, Belleville washer, socket head bolt
10. **turnbuckle.py** — Tekno TKR6250 M3 turnbuckle
11. **cable_assembly.py** — Wire rope, eye nuts, clevis pins
12. **keyboard_half.py** — 80×110×4.8mm simplified half with keycap stubs
13. **assembly.py** — 6 assembly functions, CONFIGS dict, Z-stacking positioning
14. **glb_postprocess.py** — Injects part labels into GLB JSON chunk (OCCT doesn't preserve build123d labels)
15. **build_all.py + build_single.py** — CLI build scripts
16. **test_dimensions.py** — 28 tests, all passing
17. **viewer/index.html** — Three.js GLTFLoader viewer with fold/butterfly sliders

All 6 GLBs build successfully (1–4 MB each) and render in the viewer.

## Current state — what needs to be done next

**Step 17 from PLAN.md** is defined but **not yet implemented**. It has 4 parts:

### Part A: Fix viewer rotation (`viewer/index.html`)

The `updateAngles()` function currently applies `group.rotation.z` / `group.rotation.y` directly, which rotates around the origin (0,0,0) instead of the actual pivot center at model-space (0, 0, 8.8mm). This makes keyboard halves swing through each other — physically impossible.

**Fix**: Replace with matrix-based T×R×T⁻¹ pivot rotation:
- Pivot in rootXform-local coords: `(0, 0, 0.0088)` (model Z-up, meters)
- Groups are children of `rootXform` (which carries Z-up→Y-up rotation), so children are in model-space
- Build `Matrix4`: translate to pivot → rotate → translate back
- Left: fold = `+angle/2`, butterfly = `+angle/2`; Right: negated
- Apply via `group.matrix.copy(m); group.matrixAutoUpdate = false;`

### Part B: Create `src/verification.py`

Analytical clearance checker (no AABB — too conservative for 80mm-wide boards):

1. **Fold clearance**: Rotate inner edge of each keyboard half (at X=±40mm, Z=board_bottom..board_top+keycaps) around Y at pivot Z=8.8mm. Check left inner X < right inner X at each fold step (5° increments, 0°→180°).
2. **Butterfly clearance**: Rotate disc ear tips (X=±15mm for Hirth) around Z. Check they don't reach brackets at X=±40mm (5° increments, 0°→45°).
3. Return `VerificationResult` with max achievable angles + pass/fail flags.
4. Pass criteria: fold ≥ 90°, butterfly ≥ 45°.

### Part C: Integrate into `scripts/build_all.py`

Call `verify_config(name)` after each GLB export + label injection. Fail the build if verification fails.

### Part D: Create `tests/test_physical.py`

Pure math tests (no build123d dependency):
- Rotation helper correctness (hand-computed 90° case)
- All 6 configs pass fold ≥ 90° and butterfly ≥ 45°
- PIVOT_OFFSET=4mm allows 180° fold
- Hirth ear clearance at 45° butterfly

### Implementation order

1. `src/verification.py`
2. `tests/test_physical.py` → run with `.venv/bin/python -m pytest tests/test_physical.py -v`
3. `scripts/build_all.py` → add verification call
4. `viewer/index.html` → fix `updateAngles()`
5. Rebuild all 6 GLBs → `.venv/bin/python scripts/build_all.py`
6. Manual browser check (serve with `python3 -m http.server 8084` from repo root, open `viewer/`)

## Key technical details

### Coordinate systems
- **Model space** (build123d): Z-up, millimeters
- **GLB file**: Z-up internally, but root node has quaternion `[-0.707, 0, 0, 0.707]` (90° X rotation for Z→Y conversion). Coordinates in **meters** (glTF standard).
- **Three.js viewer**: Y-up. `model.scale.setScalar(1000)` converts meters→mm for comfortable viewing.
- **rootXform children** are in model-space (Z-up, meters). The `model.scale(1000)` on the outermost node doesn't affect local transforms.

### Assembly stacking order (Z positions in mm)
```
Z = 14.8  Thumb nut
Z = 13.0  Belleville washer
Z = 12.5  Upper disc (right bracket)
Z = 10.0  Teeth mesh zone
Z =  9.5  Lower disc (left bracket)
Z =  8.8  PIVOT CENTER — fold shaft here
Z =  8.0  PHA body
Z =  4.8  Board top surface
Z =  0.0  Table
```

### Part label naming convention
- `center_*` — fixed during fold (PHA body, shaft, M4 bolt)
- `left_*` — rotates with left keyboard half
- `right_*` — rotates with right keyboard half

### GLB post-processing
build123d's OCCT glTF writer uses XDE document labels (e.g., `=>[0:1:1:2]`) as node names, not `part.label`. `glb_postprocess.py:inject_labels()` rewrites the GLB JSON chunk to replace these with our custom labels.

### Key constants from config.py
- `PIVOT_OFFSET = 4.0` mm — distance above board top to pivot center
- `STACK_Z["pivot_center"] = 8.8` mm
- Keyboard half: 80×110×4.8mm
- Hirth: 20mm OD, 9mm bore, 24 teeth, 60° V-groove
- Bracket X offset: `KeyboardHalfDims().width / 2 = 40mm`

### The 6 configurations
| Config name | Fold hinge | Butterfly joint |
|---|---|---|
| `pha-hirth` | PHA 8mm friction | Hirth 24T |
| `pha-curvic` | PHA 8mm friction | Curvic 36T |
| `pha-serrated` | PHA 8mm friction | Serrated 72T |
| `bearing-hirth` | Bearing pivot | Hirth 24T |
| `bearing-curvic` | Bearing pivot | Curvic 36T |
| `bearing-serrated` | Bearing pivot | Serrated 72T |

## Project structure

```
hinge-modelling/
├── PLAN.md                           # Full implementation plan (Steps 1-17)
├── session_handover.md               # This file
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── .venv/                            # Python 3.12 venv with build123d
├── src/
│   ├── __init__.py
│   ├── config.py                     # All dims as frozen dataclasses + COLORS + STACK_Z
│   ├── primitives.py                 # Reusable shapes
│   ├── assembly.py                   # 6 assembly functions + CONFIGS dict
│   ├── glb_postprocess.py            # GLB label injection
│   ├── keyboard_half.py              # Simplified keyboard half
│   ├── fold_hinges/
│   │   ├── pha_8mm.py                # PHA 8mm friction hinge
│   │   └── bearing_pivot.py          # Miniature bearing pivot
│   ├── butterfly_joints/
│   │   ├── hirth_24t.py              # Hirth 24T (lofted V-groove teeth)
│   │   ├── curvic_36t.py             # Curvic 36T (arc-ground teeth)
│   │   └── serrated_72t.py           # Serrated 72T + cam lever
│   ├── brackets/
│   │   └── angled_bracket.py         # 15° L-bracket pair
│   ├── clamping/
│   │   ├── thumb_nut.py              # Knurled thumb nut + Belleville washer
│   │   └── clamp_bolt.py             # M4 socket head cap screw
│   └── cables/
│       ├── turnbuckle.py             # Tekno TKR6250
│       └── cable_assembly.py         # Wire rope + eye nuts + clevis pins
├── scripts/
│   ├── build_all.py                  # Build all/specified configs → output/*.glb
│   └── build_single.py              # Build one config
├── output/                           # 6 GLB files (1-4 MB each)
│   ├── pha-hirth.glb
│   ├── pha-curvic.glb
│   ├── pha-serrated.glb
│   ├── bearing-hirth.glb
│   ├── bearing-curvic.glb
│   └── bearing-serrated.glb
├── viewer/
│   └── index.html                    # Three.js GLB viewer (has rotation bug)
└── tests/
    ├── __init__.py
    └── test_dimensions.py            # 28 tests, all passing
```

## Bugs fixed during development (for context)

- **Curvic `make_face()` ValueError**: `BuildLine` in a sub-function didn't propagate to parent `BuildSketch`. Fixed by inlining.
- **Bearing pivot bore splits solid**: Subtracting bore through full yoke (with gap between arms) produced ShapeList. Fixed by pre-drilling each arm before union.
- **Keyboard half too wide**: 6 keycap columns exceeded 80mm. Reduced to 4 columns.
- **GLB node names**: OCCT writer ignores `part.label`. Created `glb_postprocess.py`.
- **Viewer empty grid (3 rounds)**: (1) clone approach broken → reparent instead. (2) lost root transform → groups as children of rootXform. (3) coordinates in meters → `scale(1000)`.
- **Test failures**: Hirth Y extent and turnbuckle X test expectations were wrong. Fixed assertions.

## How to run

```bash
cd /home/a/git/git/keyboard/hinge-modelling

# Activate venv
source .venv/bin/activate

# Run dimensional tests
python -m pytest tests/test_dimensions.py -v

# Build all 6 GLBs
python scripts/build_all.py

# Build one config
python scripts/build_single.py pha-hirth

# Serve viewer
python3 -m http.server 8084
# Open http://localhost:8084/viewer/
```
