# Plan: Rewrite Hinge Mechanisms in build123d

## Context

The existing hinge mechanism models are built with Three.js primitives in `wip/mechanisms/demo/index.html` (approximate shapes) and `wip/hardware-builders.js` (more accurate but still limited to boxes, cylinders, tori). The user wants precise models authored with CAD-grade tooling ([build123d](https://github.com/gumyr/build123d)) that can be exported to glTF/GLB and imported into the browser Three.js visualization as the hinge mechanism geometry.

**Why build123d?** While Three.js *can* represent any mesh geometry, authoring precise mechanical parts (Hirth tooth profiles with radially-varying V-groove height, filleted edges, threaded features) requires manually computing vertex positions or writing custom parametric mesh generators. build123d provides high-level CAD operations (`loft()`, `fillet()`, `revolve()`, `PolarLocations`) purpose-built for this — making it easier to produce geometrically accurate results, and easier for the LLM to work with for this specific modelling task. The output is still a triangle mesh (glTF) that Three.js renders normally.

**Why glTF/GLB?** GLB (binary glTF) preserves part names (labels), per-part colors, and parent-child hierarchy in a single binary file. STL loses all metadata (names, colors, groups). OBJ loses hierarchy. GLB is also the native format for Three.js's `GLTFLoader`, so no conversion step is needed.

**Dimension source:** `wip/hardware-catalog.js` contains manufacturer-sourced dimensions (Reell PHA 8mm, 20mm Hirth disc with 24 teeth, Tekno TKR6250 turnbuckle, etc.). These supersede the demo's approximate values (60mm Hirth, 12 teeth).

**Per-part colors for glTF export:** build123d embeds colors via `part.color = Color(...)` which `export_gltf` maps to PBR metallic-roughness materials in glTF. Color assignments:

| Part | Color | Hex | Rationale |
|---|---|---|---|
| PHA body | Chrome matte | `#AAAAAA` | Zinc housing |
| PHA shaft / pins | Steel | `#888888` | Polished steel |
| Flag leaf | Steel | `#888888` | Same as shaft |
| Hirth discs | Dark steel | `#666666` | Hardened tool steel |
| Brackets | Light grey | `#BBBBBB` | 316L stainless |
| Thumb nut | Brass | `#CC9944` | Brass knurled nut |
| Belleville washer | Dark grey | `#555555` | Spring steel |
| M4 bolt | Steel | `#888888` | 12.9 grade |
| Turnbuckle body | Aluminum | `#CCCCCC` | Anodized aluminum |
| Keyboard halves | Bamboo | `#D4A574` | Matches existing demo |
| Mounting screws | Copper tint | `#BB7744` | Visual distinction |

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
│   │   ├── curvic_36t.py       # Curvic coupling with arc-ground teeth
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
│   │   ├── turnbuckle.py       # Tekno TKR6250 M3 turnbuckle
│   │   └── cable_assembly.py   # Wire rope + eye nuts + clevis pins
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
Ensure your verifications catch fysically impossilbe movements.  
Ensure everything is connected properly

### Step 1: Project setup
- Create `pyproject.toml` with `build123d` dependency
- Create `requirements.txt` as fallback
- Create `.gitignore` (ignoring `output/*.glb`, `__pycache__/`, `*.egg-info/`, `.venv/`)
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
The V-groove tooth profile varies in height from bore (0.7mm) to OD (2.3mm).

Flank angle β = arcsin(tan(π/48) / tan(30°)) ≈ 13.17° — this is computed, not approximated.

**Tooth construction strategy** (precise):

1. Create base ring: `Cylinder(10, 5) - Cylinder(4.5, 5)` (OD=20mm, bore=9mm, total disc thickness 5mm)
2. Build ONE tooth sector (15° angular span = 360°/24):
   a. On a radial plane at the inner bore (r=4.5mm), define a triangular cross-section: an isosceles triangle with base = arc length at bore (r × 15° ≈ 1.18mm) and height = 0.7mm (tooth height at ID)
   b. On a radial plane at the outer edge (r=10mm), define a triangular cross-section: base = arc length at OD (r × 15° ≈ 2.62mm) and height = 2.3mm (tooth height at OD)
   c. `loft()` between the inner and outer triangular profiles to create a single tapered V-groove tooth solid
3. Use `PolarLocations(radius=0, count=24)` to replicate the tooth 24 times around the disc center axis, unioning all teeth onto the base ring
4. Subtract the central bore: `Cylinder(4.5, full_height)` through the entire part
5. Add 2× mounting ears (Box 5×6×2mm) with M2 holes (`Hole(1.0)`) extending beyond OD at 0° and 180°
6. Create matched pair: one disc with teeth facing +Z (lower), one with teeth facing -Z (upper, mirrored)

### Step 6: `butterfly_joints/curvic_36t.py` — Curvic coupling
Similar to Hirth but with arc-ground teeth (concave on one disc, convex on the other):
- OD=22mm, bore=9mm, 36 teeth (10° resolution), tooth height at OD=1.8mm
- Tooth profile: circular arcs with grinding wheel radius 12mm (from `CurvicDims.toothArcRadius`)
- One disc has concave arc teeth, the other convex — they self-center under axial load
- Construction: define arc cross-section (using `CenterArc` in BuildLine), sweep radially, polar-pattern 36×
- Same mounting ears and matched pair approach as Hirth
- Dims from `CurvicDims` in config.py (lines 121-138 of hardware-catalog.js)

### Step 7: `brackets/angled_bracket.py` — L-shaped bracket
- Flange: `Box(10, 12, 2)` lies flat on board edge
- Arm: `Box(15.5, 12, 2)` rotated 15° from horizontal
- Fillet at the bend
- 2× M2.5 holes at 8mm spacing through flange
- Build as a pair (left/right mirror)

### Step 8: `clamping/` — Thumb nut + bolt + washer
- **Thumb nut**: `Cylinder(7, 8)` (14mm OD, 8mm height) with knurled surface + M4 threaded bore
- **Belleville washer**: revolve conical annular section (M4 bore, ~9mm OD)
- **M4 bolt**: `Cylinder(2, 20)` + `hex_prism(7, 3.2)` socket head

### Step 9: `cables/turnbuckle.py` — Tekno TKR6250
- Body: `Cylinder(2.75, 20)` hexagonal (or hex prism)
- Rods: 2× `Cylinder(1.5, 17.5)` extending from body ends
- Eyes: 2× `Torus(2, 1.15)` at each end

### Step 10: `cables/cable_assembly.py` — Wire rope + eye nuts + clevis pins
- **Wire rope**: `Cylinder(0.75, length)` (1.5mm dia from catalog) connecting keyboard halves, 2 cables (near/far)
- **Eye nuts**: M3 304SS lifting eye nut — ring (`Torus(6.5, 2.875)`) + hex nut base (`hex_prism(5.5, 2.4)`) + threaded stud (`Cylinder(1.5, 8)`)
- **Clevis pins**: 5mm ball-lock pin — shaft `Cylinder(2.5, 15)` + body `Cylinder(4.5, 12)` + button `Cylinder(3.25, 3)`
- Dims from `EyeNutDims` and `ClevisPinDims` in config.py

### Step 11: `keyboard_half.py` — Simplified half
- Body: `Box(80, 110, 4.8)` in bamboo color
- Optional: 18 keycap stubs as small raised boxes

### Step 12: `assembly.py` — Compose and position
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

Group parts for animation using a label naming convention with `center_`, `left_`, `right_` prefixes. The Three.js consumer traverses the loaded glTF scene and groups meshes by prefix for fold/butterfly rotation:

- **`center_` group** (stays fixed during fold): `center_pha_body`, `center_pha_shaft`, `center_m4_bolt`
- **`left_` group** (rotates with left half): `left_bracket`, `left_hirth_disc`, `left_keyboard_half`
- **`right_` group** (rotates with right half): `right_bracket`, `right_hirth_disc`, `right_thumb_nut`, `right_keyboard_half`

In build123d, each `Part` gets its label set before being added to the assembly `Compound`:
```python
shaft.label = "center_pha_shaft"
left_disc.label = "left_hirth_disc"
```

The Three.js loader groups by prefix:
```javascript
model.traverse((child) => {
    if (child.name.startsWith('center_')) centerGroup.add(child);
    else if (child.name.startsWith('left_')) leftGroup.add(child);
    else if (child.name.startsWith('right_')) rightGroup.add(child);
});
```

### Step 13: Export pipeline
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

### Step 14: `viewer/index.html` — Standalone test viewer (does NOT replace existing demo)

**Important**: The existing keyboard visualization (`wip/wizard.html`, `wip/render3d.js`, `wip/mechanisms/demo/index.html`) remains **unchanged**. The whole keyboard is auto-generated from finger position data, and the 3D hardware is computed from that data — that pipeline stays as-is. This viewer is a standalone test page within the `hinge-modelling` repo, used only to verify the GLB exports look correct before integrating them.

The GLB models produced here will eventually be **imported into** the existing `wip/render3d.js` keyboard visualization via `GLTFLoader`, replacing only the hinge mechanism geometry (currently built with Three.js primitives in `hardware-builders.js`). The rest of the keyboard render is untouched.

**Mechanical interface consistency**: The bracket mounting holes (2× M2.5 at 8mm spacing) and their position on the keyboard half's inner edge must match between:
- The build123d bracket models (this repo) — holes modelled in `angled_bracket.py`
- The keyboard half's generated hardware (in `wip/`) — matching threaded insert positions

Both reference the same dimensions from `hardware-catalog.js` (`BracketDims`), ensuring the hinge models attach harmoniously to the keyboard halves.

Minimal test viewer features:
- `GLTFLoader` loading `output/pha-hirth.glb`
- Fold angle slider (0-180°) — rotates left/right groups around Y at pivot center
- Butterfly angle slider (0-45°) — rotates groups around Z
- Camera presets
- Part names from build123d labels (prefix convention) used to identify groups for animation

### Step 15: `scripts/build_all.py` — CLI entry point
```bash
python scripts/build_all.py              # builds all 6 configs
python scripts/build_single.py pha-hirth # builds one
```

### Step 16: Dimensional tests
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

---

## Step 17: Physical Plausibility Verification + Viewer Fix

### Context

The 3D viewer applies fold and butterfly rotations at the group origin (0,0,0) instead of around the actual pivot center at model-space (0, 0, 8.8mm). This causes keyboard halves to swing through each other — physically impossible. The user wants:
1. Fix the viewer so rotations happen around the correct pivot
2. Add a build-time verification check that rejects physically impossible folding for every configuration

3. DO not only check if the keyboard halves bump into eachother, but also check if hinge components collide.

### Root cause

- **Viewer**: `updateAngles()` applies `group.rotation.z` (fold) and `group.rotation.y` (butterfly) but groups sit at origin — rotation orbits around (0,0,0) not the pivot at (0, 0, 0.0088m) in model-space (Z-up, meters)
- **No verification**: The build pipeline has no collision/clearance checks

### Files to modify/create

| File | Action |
|------|--------|
| `viewer/index.html` | Fix `updateAngles()` — matrix-based pivot rotation |
| `src/verification.py` | **New** — analytical clearance checker |
| `scripts/build_all.py` | Add verification call after each GLB export |
| `tests/test_physical.py` | **New** — tests for verification module |

### Part A: Fix viewer rotation (`viewer/index.html`)

Replace `updateAngles()` with matrix-based pivot rotation:

1. Define pivot in rootXform-local coords: `PIVOT = (0, 0, 0.0088)` (model Z-up, meters)
2. For each group (left/right), build a `Matrix4`:
   - Translate to pivot → rotate (fold around Y, butterfly around Z, Euler order `YZX`) → translate back
3. Apply via `group.matrix.copy(m); group.matrixAutoUpdate = false;`
4. Left: fold = `+angle/2`, butterfly = `+angle/2`; Right: negated

Key coordinate insight: groups are children of `rootXform` (which carries the Z-up→Y-up rotation). Children are in model-space (Z-up, meters). The `model.scale(1000)` on the outermost node doesn't affect local transforms.

### Part B: Build-time verification (`src/verification.py`)

**Analytical geometry** — no AABB (too conservative for 80mm-wide keyboard halves):

1. **Fold clearance**: Rotate inner edge of each keyboard half (at X=±40mm, Z=board_bottom..board_top+keycaps) around Y at pivot Z=8.8mm. Check left inner X < right inner X at each fold step.
2. **Butterfly clearance**: Rotate disc ear tips (X=±15mm for Hirth) around Z. Check they don't reach brackets at X=±40mm.
3. Sweep fold 0°→180° in 5° steps, butterfly 0°→45° in 5° steps.
4. Return `VerificationResult` with max achievable angles + pass/fail flags.
5. Pass criteria: fold ≥ 90° (REQ-M03a), butterfly ≥ 45°.

Expected results: PIVOT_OFFSET=4mm gives ~4mm lateral clearance at 180° fold → all configs should pass comfortably. Disc ears at 15mm max are far from brackets at 40mm → butterfly 45° passes easily.

### Part C: Build integration (`scripts/build_all.py`)

After each successful GLB export + label injection, call `verify_config(name)`. Print results. Return `False` (fail the build) if verification fails.

### Part D: Tests (`tests/test_physical.py`)

- Rotation helper correctness (hand-computed 90° case)
- All 6 configs pass fold ≥ 90° and butterfly ≥ 45°
- PIVOT_OFFSET=4mm allows 180° fold (key design parameter)
- Hirth ear clearance at 45° butterfly
- Pure math tests (no build123d imports) — fast execution

### Implementation order

1. `src/verification.py`
2. `tests/test_physical.py` → run pytest
3. `scripts/build_all.py` → add verification import + call
4. `viewer/index.html` → fix `updateAngles()`
5. Rebuild all 6 GLBs → verify pass
6. Manual browser check

### Verification

```bash
# Run verification tests
.venv/bin/python -m pytest tests/test_physical.py -v

# Rebuild with verification
.venv/bin/python scripts/build_all.py

# Visual check: open viewer, fold to 90°, confirm halves tent correctly
```

---

## Step 18: Fix Cable/Turnbuckle Collision During Fold

### Context

Step 17 fixed pivot-based rotation so keyboard halves fold correctly, but revealed a new issue: the cable assembly (2 wire ropes + turnbuckle) clips through itself during fold. The cables are single full-width cylinders labeled `center_cable_*` (stay fixed), and the turnbuckle is `center_turnbuckle` (also fixed). When the halves tent upward, these rigid center-group rods remain horizontal and visibly intersect.

### Root cause

In `src/cables/cable_assembly.py`, `build_cable()` creates a single `Cylinder` spanning the full `cable_length` (200mm) along X, labeled `center_cable`. Since center-group parts don't participate in fold rotation, the cables stay flat while everything else tents upward.

The turnbuckle (`src/cables/turnbuckle.py`) is similarly a single `center_turnbuckle` part — 55mm eye-to-eye along X, fixed at Y=60mm. It's smaller and further from center, but suffers the same issue.

Eye nuts and clevis pins already have `left_`/`right_` labels but aren't positioned at the cable endpoints — they're all placed at origin (the assembly positions them at a flat Z offset but no meaningful X).

### Fix

#### Part A: Split cables into left/right halves (`src/cables/cable_assembly.py`)

Replace each full-width cable with two half-cables split at X=0:
- Left half: `Cylinder(r, cable_length/2)` centered at `X = -cable_length/4`, labeled `left_cable_N`
- Right half: same, centered at `X = +cable_length/4`, labeled `right_cable_N`

Remove the `build_cable()` helper (no longer needed — inline the half-cable creation).

Position eye nuts at the cable endpoints:
- Left eye nuts at `X = -cable_length/2` (outer end of left cable)
- Right eye nuts at `X = +cable_length/2` (outer end of right cable)

Position clevis pins similarly at cable endpoints, oriented along Z (vertical, into the board).

#### Part B: Split turnbuckle into left/right halves (`src/cables/turnbuckle.py`)

Change `build_turnbuckle()` to return a `list[Part]` (2 halves) instead of a single Part:
- Left half: left rod + left eye + left half of body → labeled `left_turnbuckle`
- Right half: right rod + right eye + right half of body → labeled `right_turnbuckle`

The body split is at X=0: two `hex_prism` halves of `body_len/2` each, offset to `X = ∓body_len/4`.

#### Part C: Update assembly (`src/assembly.py`)

Adapt `assemble_pha_hirth()` (the only config using cables/turnbuckle):
- `build_turnbuckle()` now returns a list — iterate and position each half
- `build_cable_assembly()` already returns a list — labels are now `left_`/`right_` so no assembly changes needed beyond turnbuckle handling

#### Part D: Update turnbuckle test (`tests/test_dimensions.py`)

The `TestTurnbuckle::test_eye_to_eye` test measures the bounding box of the single turnbuckle part. With the split, it needs to measure the combined extent of both halves, or test each half individually.

### Files to modify

| File | Action |
|------|--------|
| `src/cables/cable_assembly.py` | Split cables, position eye nuts + clevis pins at endpoints |
| `src/cables/turnbuckle.py` | Split into left/right halves, return `list[Part]` |
| `src/assembly.py` | Handle `build_turnbuckle()` returning a list |
| `tests/test_dimensions.py` | Update turnbuckle test for split parts |

### Implementation order

1. `src/cables/turnbuckle.py` — split into 2 halves
2. `src/cables/cable_assembly.py` — split cables, position hardware at endpoints
3. `src/assembly.py` — update turnbuckle handling
4. `tests/test_dimensions.py` — fix turnbuckle test
5. Run all tests → `.venv/bin/python -m pytest tests/ -v`
6. Rebuild all 6 GLBs → `.venv/bin/python scripts/build_all.py`
7. Visual check in viewer — fold to 90°, confirm cables/turnbuckle tent with halves

### Verification

```bash
# Run all tests
.venv/bin/python -m pytest tests/ -v

# Rebuild with verification
.venv/bin/python scripts/build_all.py

# Visual check: fold to 90°, cables and turnbuckle should tent with halves
```
