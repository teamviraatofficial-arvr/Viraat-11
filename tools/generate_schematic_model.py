#!/usr/bin/env python3
"""
Generate a compact, schematic glTF 2.0 model (model.gltf + model.bin), a 512x512 preview PNG,
metadata.json and a zip package containing all artifacts.

Usage:
  python tools/generate_schematic_model.py --id model_id --name "Model Name"

Dependencies:
  - Python 3.8+
  - Pillow (optional, to generate the preview PNG). If Pillow is missing, a minimal placeholder PNG will be created.

Safety: This script generates schematic, non-functional geometry only and embeds metadata marking
"safety_level": "educational".
"""

import argparse
import json
import math
import os
import struct
import zipfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# Simple helper to create a unit cube centered at origin
def create_box(center, size):
    cx, cy, cz = center
    sx, sy, sz = size
    # 8 vertices
    x = sx / 2.0
    y = sy / 2.0
    z = sz / 2.0
    verts = [
        (cx - x, cy - y, cz + z),
        (cx + x, cy - y, cz + z),
        (cx + x, cy + y, cz + z),
        (cx - x, cy + y, cz + z),
        (cx - x, cy - y, cz - z),
        (cx + x, cy - y, cz - z),
        (cx + x, cy + y, cz - z),
        (cx - x, cy + y, cz - z),
    ]
    # Triangles (two per face) using uint16 indices
    indices = [
        0,1,2, 0,2,3,  # front
        4,6,5, 4,7,6,  # back
        4,5,1, 4,1,0,  # bottom
        3,2,6, 3,6,7,  # top
        1,5,6, 1,6,2,  # right
        4,0,3, 4,3,7,  # left
    ]
    return verts, indices

# Flatten arrays and build binary buffer
def build_buffer_for_meshes(meshes):
    # meshes: list of dicts with 'positions' list[(x,y,z)] and 'indices' list[int]
    buffer_bytes = bytearray()
    buffer_views = []
    accessors = []

    # We'll create for each mesh: positions (float32), indices (uint16)
    for m in meshes:
        # positions
        pos_offset = len(buffer_bytes)
        for (x,y,z) in m['positions']:
            buffer_bytes += struct.pack('<fff', float(x), float(y), float(z))
        pos_length = len(m['positions']) * 12  # 3 * 4 bytes

        # create bufferView for positions
        buffer_views.append({
            'buffer': 0,
            'byteOffset': pos_offset,
            'byteLength': pos_length,
            'target': 34962 # ARRAY_BUFFER
        })
        accessor_pos_index = len(accessors)
        accessors.append({
            'bufferView': len(buffer_views)-1,
            'byteOffset': 0,
            'componentType': 5126, # FLOAT
            'count': len(m['positions']),
            'type': 'VEC3',
            'min': [min(p[i] for p in m['positions']) for i in range(3)],
            'max': [max(p[i] for p in m['positions']) for i in range(3)],
        })

        # indices (uint16)
        idx_offset = len(buffer_bytes)
        for idx in m['indices']:
            buffer_bytes += struct.pack('<H', int(idx))
        idx_length = len(m['indices']) * 2

        buffer_views.append({
            'buffer': 0,
            'byteOffset': idx_offset,
            'byteLength': idx_length,
            'target': 34963 # ELEMENT_ARRAY_BUFFER
        })
        accessor_idx_index = len(accessors)
        accessors.append({
            'bufferView': len(buffer_views)-1,
            'byteOffset': 0,
            'componentType': 5123, # UNSIGNED_SHORT
            'count': len(m['indices']),
            'type': 'SCALAR'
        })

        # record indexes for mesh construction
        m['accessor_pos'] = accessor_pos_index
        m['accessor_idx'] = accessor_idx_index

    # Return buffer bytes and glTF bufferViews/accessors
    return bytes(buffer_bytes), buffer_views, accessors


def normalize_scale(meshes):
    # scale meshes so longest dimension = 1.0
    all_coords = []
    for m in meshes:
        for p in m['positions']:
            all_coords.append(p)
    xs = [c[0] for c in all_coords]
    ys = [c[1] for c in all_coords]
    zs = [c[2] for c in all_coords]
    if not xs:
        return meshes
    span_x = max(xs)-min(xs)
    span_y = max(ys)-min(ys)
    span_z = max(zs)-min(zs)
    longest = max(span_x, span_y, span_z)
    if longest == 0:
        return meshes
    scale = 1.0 / longest
    for m in meshes:
        m['positions'] = [(x*scale, y*scale, z*scale) for (x,y,z) in m['positions']]
    return meshes


def generate_preview_png(out_path, model_name):
    # Simple schematic thumbnail: rectangles for body and accessories
    size = (512,512)
    if PIL_AVAILABLE:
        img = Image.new('RGBA', size, (10,14,39,255))
        draw = ImageDraw.Draw(img)
        # body: center rectangle
        draw.rectangle([156,156,356,356], fill=(0,212,170,255))
        # accessory_1
        draw.rectangle([360,220,430,290], fill=(141,85,36,255))
        # accessory_2
        draw.rectangle([80,220,150,290], fill=(51,51,51,255))
        # text label
        try:
            font = ImageFont.truetype('DejaVuSans.ttf', 18)
        except Exception:
            font = ImageFont.load_default()
        text = (model_name or 'schematic').upper()
        # Determine text size robustly across Pillow versions
        try:
            w, h = font.getsize(text)
        except Exception:
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except Exception:
                w, h = 200, 20
        draw.text(((512-w)/2, 12), text, fill=(255,255,255,220), font=font)
        img.save(out_path)
    else:
        # If Pillow not available, write a small single-color PNG data (512x512) using a minimal precomputed base64.
        # We'll emit a tiny 1x1 PNG scaled metadata is not possible; instead create a minimal binary placeholder (not a valid image)
        with open(out_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n')
            f.write(b'Placeholder preview - install Pillow to generate real PNG')


def write_gltf(out_dir, meshes, buffer_bytes):
    # Build glTF JSON structure with one buffer (external bin file)
    buffer_uri = 'model.bin'
    buffer_length = len(buffer_bytes)

    # Prepare bufferViews and accessors from mesh dicts
    buffer_views = []
    accessors = []
    # The meshes already contain accessor indices as set by build_buffer_for_meshes
    # We'll recompute the bufferViews/accessors again using the helper to ensure order
    # But for simplicity, call build_buffer_for_meshes already produced those arrays, so they were returned.
    # To avoid complexity, we will call build_buffer_for_meshes earlier and pass buffer_views/accessors
    raise RuntimeError('write_gltf should be called with pre-computed bufferViews/accessors')


def build_gltf_json(meshes, buffer_views, accessors, model_id, model_name):
    # Create glTF dict using provided bufferViews and accessors
    gltf = {
        'asset': {'version': '2.0', 'generator': 'schematic-generator'},
        'scenes': [{'nodes': [0,1,2]}],
        'scene': 0,
        'nodes': [],
        'meshes': [],
        'buffers': [{'uri': 'model.bin', 'byteLength': 0}],
        'bufferViews': buffer_views,
        'accessors': accessors,
    }
    # Create one mesh per logical part, each mesh will contain two primitives (high & low LOD)
    for m in meshes:
        # Each primitive uses the stored accessor indices
        prim_high = {
            'attributes': {
                'POSITION': m['accessor_pos']
            },
            'indices': m['accessor_idx'],
            'mode': 4 # TRIANGLES
        }
        # Low LOD: for this simple generator we'll point to same geometry (clients can choose to use primitive 1)
        prim_low = {
            'attributes': {
                'POSITION': m['accessor_pos']
            },
            'indices': m['accessor_idx'],
            'mode': 4
        }
        gltf['meshes'].append({
            'name': m['name'] + '_mesh',
            'primitives': [prim_high, prim_low],
            'extras': {'lod_primitives': {'high': 0, 'low': 1}}
        })

    # Nodes for scene, referencing each mesh
    for i, m in enumerate(meshes):
        gltf['nodes'].append({'name': m['name'], 'mesh': i})

    # Fill buffer byteLength
    total_buf_len = sum(bv['byteLength'] for bv in buffer_views)
    gltf['buffers'][0]['byteLength'] = total_buf_len

    # Add simple materials (flat PBR) and assign a material to each primitive via material index
    # For simplicity we'll create materials but not reference them explicitly (optional enhancement)

    return gltf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True, help='Model ID (used in filenames)')
    parser.add_argument('--name', required=False, default='', help='Model display name')
    parser.add_argument('--out', required=False, default='.', help='Output directory')
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_id = args.id
    model_name = args.name or args.id

    # Define three box parts positioned along X axis
    body_verts, body_indices = create_box((0.0, 0.0, 0.0), (1.0, 0.6, 0.4))
    acc1_verts, acc1_indices = create_box((0.8, -0.1, 0.0), (0.3, 0.25, 0.1))
    acc2_verts, acc2_indices = create_box((-0.8, -0.1, 0.0), (0.25, 0.2, 0.1))

    meshes = [
        {'name': 'body', 'positions': body_verts, 'indices': body_indices},
        {'name': 'accessory_1', 'positions': acc1_verts, 'indices': acc1_indices},
        {'name': 'accessory_2', 'positions': acc2_verts, 'indices': acc2_indices},
    ]

    # Normalize scale so longest dimension == 1.0
    meshes = normalize_scale(meshes)

    # Build binary buffer and obtain bufferViews/accessors
    buffer_bytes, buffer_views, accessors = build_buffer_for_meshes(meshes)

    # Build glTF JSON
    gltf = build_gltf_json(meshes, buffer_views, accessors, model_id, model_name)

    # Write model.bin
    bin_path = out_dir / 'model.bin'
    with open(bin_path, 'wb') as f:
        f.write(buffer_bytes)

    # Write model.gltf
    gltf_path = out_dir / 'model.gltf'
    with open(gltf_path, 'w', encoding='utf-8') as f:
        json.dump(gltf, f, indent=2)

    # Write metadata.json
    metadata = {
        'model_id': model_id,
        'model_name': model_name,
        'source': 'antigravity',
        'safety_level': 'educational'
    }
    with open(out_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    # Generate preview PNG
    preview_path = out_dir / 'preview.png'
    generate_preview_png(preview_path, model_name)

    # Package into zip
    zip_path = out_dir / f"{model_id}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(gltf_path, arcname='model.gltf')
        z.write(bin_path, arcname='model.bin')
        z.write(preview_path, arcname='preview.png')
        z.write(out_dir / 'metadata.json', arcname='metadata.json')

    print('Generated package:', zip_path)
    print('Notes: This asset is schematic and marked as educational. It contains no functional internals or assembly instructions.')

if __name__ == '__main__':
    main()
