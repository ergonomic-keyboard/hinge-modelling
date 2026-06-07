"""Post-process GLB files to inject part names from build123d labels.

The OCCT glTF writer doesn't preserve build123d part labels — node names
are OCCT XDE document labels like "=>[0:1:1:2]". This module rewrites the
GLB's JSON chunk to replace those with our custom labels.

Node structure pattern (from OCCT writer):
    node[0] = root (children=[1, 3, 5, ...])
    node[1] = part_0_parent (children=[2])
    node[2] = part_0_mesh (mesh=0)
    node[3] = part_1_parent (children=[4])
    node[4] = part_1_mesh (mesh=1)
    ...

We rename both the parent and mesh nodes for each part.
"""

import json
import struct
from pathlib import Path


def inject_labels(glb_path: str | Path, labels: list[str]) -> None:
    """Rewrite GLB file in-place, setting node names from labels.

    Args:
        glb_path: Path to the .glb file
        labels: List of part labels, in the same order as parts were
                added to the Compound
    """
    glb_path = Path(glb_path)

    with open(glb_path, "rb") as f:
        # GLB header: magic(4) + version(4) + length(4)
        magic = f.read(4)
        assert magic == b"glTF", f"Not a GLB file: {magic}"
        version = struct.unpack("<I", f.read(4))[0]
        total_length = struct.unpack("<I", f.read(4))[0]

        # JSON chunk: length(4) + type(4) + data(length)
        json_chunk_len = struct.unpack("<I", f.read(4))[0]
        json_chunk_type = f.read(4)
        assert json_chunk_type == b"JSON"
        json_data = f.read(json_chunk_len)

        # Binary chunk: rest of file
        remaining = f.read()

    gltf = json.loads(json_data)
    nodes = gltf.get("nodes", [])

    if not nodes:
        return

    # Find the root node (has children but no mesh)
    root = nodes[0]
    children_indices = root.get("children", [])

    # Each child index points to a parent node that wraps a mesh node
    for i, child_idx in enumerate(children_indices):
        if i >= len(labels):
            break
        label = labels[i]
        if not label:
            continue

        # Rename the parent node
        nodes[child_idx]["name"] = label

        # Rename the mesh node (child of parent)
        mesh_children = nodes[child_idx].get("children", [])
        if mesh_children:
            nodes[mesh_children[0]]["name"] = f"{label}_mesh"

    # Rewrite the GLB
    new_json = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    # Pad to 4-byte alignment
    padding = (4 - len(new_json) % 4) % 4
    new_json += b" " * padding

    new_json_len = len(new_json)

    with open(glb_path, "wb") as f:
        # Header
        new_total = 12 + 8 + new_json_len + len(remaining)
        f.write(b"glTF")
        f.write(struct.pack("<I", version))
        f.write(struct.pack("<I", new_total))

        # JSON chunk
        f.write(struct.pack("<I", new_json_len))
        f.write(b"JSON")
        f.write(new_json)

        # Binary chunk (unchanged)
        f.write(remaining)
