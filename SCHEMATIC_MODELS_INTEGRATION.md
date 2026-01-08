# Schematic 3D Models Integration Guide

## Overview

This document describes the complete pipeline for generating, integrating, and serving educational schematic 3D models in glTF 2.0 format for the VIRAAT military AI assistant.

## What Happens (End-to-End Flow)

### 1. **Model Generation** (`tools/generate_schematic_model.py`)
- **Input**: model ID + name (e.g., `--id bunker --name "Reinforced Bunker"`)
- **Process**:
  - Generates simplified box-based geometry (body, accessory_1, accessory_2)
  - Normalizes scale so longest dimension = 1.0
  - Creates two LOD (level-of-detail) primitives per mesh
  - Builds binary buffer (model.bin) with float32 positions and uint16 indices
  - Generates glTF JSON structure (model.gltf) conforming to glTF 2.0 spec
  - Creates preview PNG (512×512) showing schematic representation
  - Generates metadata.json with safety flags and provenance
  - Packages all files into a zip archive
- **Output**:
  ```
  output/{model_id}/
  ├── model.gltf          (glTF 2.0 JSON structure, ~2-5 KB)
  ├── model.bin           (binary buffer, ~2-5 KB)
  ├── preview.png         (512x512 preview, ~10-30 KB)
  ├── metadata.json       (provenance/safety, ~0.5 KB)
  └── {model_id}.zip      (packaged artifact, ~15-50 KB)
  ```

### 2. **Backend Processing** (`backend/main.py`)
- **Chat request arrives**: `/api/v1/chat?query="Show me a bunker"`
- **Visual intent analysis**: `visual_controller.analyze(query)` detects keywords and matches model registry
- **Response structure**:
  - Text response (from LLM or Decision Engine)
  - `visual_directive` JSON: `{ model_id, model_name, asset_path, safety_note }`
  - Returns `{ "response": "...", "sources_count": N, "visual_directive": {...} }`

### 3. **Frontend Handling** (`web/js/chat.js` + `web/js/visualizer.js`)
- **Chat.js parses response**:
  - Extracts `visual_directive` from structured JSON (not embedded markers)
  - Displays text to user immediately
  - Calls `VisualizerModule.loadModel(model_id, model_name, asset_path)`
- **Visualizer.js loads asset**:
  - If `asset_path` provided and GLTFLoader available: attempt to load glTF from path
  - On success: render glTF model with LOD selection, wireframe toggle, rotation
  - On failure: fallback to procedural geometry generation
  - Display model in split-view 3D canvas

## Why Each Component Exists

| Component | Purpose | Safety Rationale |
|-----------|---------|------------------|
| **Schematic geometry only** | Simplified silhouettes, no internal mechanisms | Prevents operational detail extraction |
| **≤10k triangles** | Small file size, cross-platform performance | Ensures fast distribution and reduces attack surface |
| **Named nodes** (`body`, `accessory_1`, `accessory_2`) | Deterministic asset structure | Enables UI labeling, LOD swapping without brittle parsing |
| **Flat PBR, no textures** | Minimal detail, quick rendering | Avoids photorealism that could reveal sensitive info |
| **Normalized scale (1.0)** | Consistent framing across assets | Simplifies viewer code and prevents scale-based reconstruction |
| **Two LODs** | High for detail, low for thumbnails | Performance scaling without asset duplication |
| **Embedded metadata.json** | Provenance and safety flags | Auditing, filtering, and legal compliance |
| **Structured JSON response** | Clean backend→frontend contract | Prevents fragile string parsing and enables future extensions |
| **Asset path in registry** | Deterministic URL mapping | Enables CDN caching and avoids dynamic generation overhead |

## How to Use

### Step 1: Generate a Model Package

```bash
cd /workspaces/Viraat-11
python3 -m pip install --user Pillow  # Optional: for PNG preview rendering
python3 tools/generate_schematic_model.py --id bunker --name "Reinforced Bunker" --out output/bunker
```

**Output**: `output/bunker/bunker.zip` containing model.gltf, model.bin, preview.png, metadata.json

### Step 2: Deploy Model Artifact

Copy the model files into the web server's static directory:

```bash
# Create directory structure
mkdir -p viraat-military-ai/web/models/bunker

# Extract and copy files
unzip output/bunker/bunker.zip -d viraat-military-ai/web/models/bunker/

# Verify
ls -la viraat-military-ai/web/models/bunker/
# Should show: model.gltf, model.bin, preview.png, metadata.json
```

### Step 3: Verify glTF Validity

Install the Khronos glTF validator (optional but recommended):

```bash
npm install -g gltf-validator  # Requires Node.js

gltf-validator viraat-military-ai/web/models/bunker/model.gltf
# Expected output: validation report; no critical errors
```

### Step 4: Backend Registry Update

The backend already includes asset paths in `visual_controller.py`:

```python
"bunker": {
    "id": "bunker",
    "type": "structure",
    "name": "Reinforced Bunker",
    "asset_path": "/models/bunker/model.gltf"
}
```

**No code changes needed** — just ensure files exist at `/models/{id}/model.gltf`.

### Step 5: Test End-to-End

1. **Start backend**:
   ```bash
   cd viraat-military-ai/backend
   source .venv/bin/activate
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start frontend server**:
   ```bash
   cd viraat-military-ai/web
   python3 -m http.server 3000
   ```

3. **Open browser** and navigate to `http://localhost:3000`

4. **Send query**: "Show me a bunker schematic"
   - Expected: Text response + 3D model rendered in visualizer

## API Contract

### Backend Response

```json
{
  "response": "Here is a schematic of a reinforced bunker...",
  "sources_count": 2,
  "visual_directive": {
    "type": "3d_view",
    "model_id": "bunker",
    "model_type": "structure",
    "model_name": "Reinforced Bunker",
    "asset_path": "/models/bunker/model.gltf",
    "safety_note": "This model is for educational/visualization use only; operational details withheld."
  }
}
```

### Frontend Handling (visualizer.js)

```javascript
// If visual_directive present:
VisualizerModule.loadModel(
  model_id,          // "bunker"
  model_name,        // "Reinforced Bunker"
  asset_path         // "/models/bunker/model.gltf"
);

// Fallback: if asset_path missing or glTF load fails:
VisualizerModule.loadProceduralModel(model_id);  // Procedural generation
```

## File Structure After Integration

```
viraat-military-ai/
├── web/
│   ├── models/
│   │   ├── bunker/
│   │   │   ├── model.gltf
│   │   │   ├── model.bin
│   │   │   ├── preview.png
│   │   │   └── metadata.json
│   │   ├── ak47/
│   │   │   └── (files...)
│   │   └── t90/
│   │       └── (files...)
│   ├── js/
│   │   ├── visualizer.js        (updated: GLTFLoader support)
│   │   └── chat.js              (updated: structured visual_directive)
│   └── index.html               (updated: GLTFLoader script tag)
├── backend/
│   ├── controllers/
│   │   └── visual_controller.py (updated: asset_path in registry)
│   └── main.py                  (updated: return visual_directive JSON)
├── tools/
│   └── generate_schematic_model.py  (new: model generator)
└── output/
    └── bunker/
        ├── model.gltf, model.bin, preview.png, metadata.json
        └── bunker.zip
```

## Verification Checklist

- [ ] `model.gltf` is valid JSON and conforms to glTF 2.0 spec
- [ ] `model.bin` exists and byteLength matches glTF buffer declaration
- [ ] Triangle count ≤ 10,000 (validate with `gltf-validator`)
- [ ] Nodes named: `body`, `accessory_1`, `accessory_2`
- [ ] Materials use metallic-roughness PBR (no textures)
- [ ] Scale normalized (longest dimension = 1.0)
- [ ] Metadata contains: `model_id`, `model_name`, `source: "antigravity"`, `safety_level: "educational"`
- [ ] Preview PNG renders correctly (512×512)
- [ ] Backend `/api/v1/chat` returns structured `visual_directive` JSON
- [ ] Frontend loads glTF via GLTFLoader with fallback to procedural generation

## Safety & Policy Notes

- **No operational details**: Geometry is schematic only; no internal mechanisms, manufacturing measurements, or functional specifications.
- **Educational use only**: Metadata flags models as `safety_level: "educational"`. UI displays advisory: "This model is for educational/visualization use only; operational details withheld."
- **Compliance**: Embeds safety note in model data for auditing and filtering.
- **Fallback safety**: If glTF loading fails, procedural generation provides minimal non-functional schematic.

## Future Enhancements

1. **Batch generation**: Add `generate_batch.py` to produce multiple models from config YAML
2. **LOD optimization**: Use glTF quantization or octree simplification for true LOD variants
3. **Texture PBR**: Allow optional low-res PBR textures (no details, flat colors)
4. **Animation support**: Add turntable rotation animation data in glTF
5. **Metadata extensions**: Add cost, timeline, historical provenance in metadata
6. **CDN integration**: Deploy models to CDN and update registry with CDN URLs
7. **Validation automation**: Add CI/CD step to validate all models on commit

## Support & Troubleshooting

| Issue | Solution |
|-------|----------|
| glTF fails to load in browser | Check browser console for CORS errors; ensure static serving configured for `/models/` |
| Model appears tiny or huge | Verify scale normalization in generator; check camera position in visualizer |
| GLTFLoader not defined | Ensure `GLTFLoader.js` script tag in index.html is loaded before visualizer.js |
| No visual_directive returned | Check `visual_controller.py` registry for keyword match; verify `asset_path` field populated |
| Procedural fallback used instead of glTF | Check browser Network tab for failed glTF request; verify file path and CORS headers |

---

**Generated**: January 2026  
**Purpose**: Educational 3D schematic visualization for military decision support  
**Safety Level**: Educational (non-operational)
