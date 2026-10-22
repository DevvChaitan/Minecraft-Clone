# 3D Minecraft Clone in Python (MCPY)

A feature-complete 3D Minecraft Alpha clone written in Python using modern OpenGL via `pyglet`, strictly following the architecture and implementation by obiwac.

![Minecraft Clone Preview](textures/grass.png)

---

## Features

- **Modern OpenGL 3.3 Core Profile**: Vertex Array Objects (VAO), Vertex Buffer Objects (VBO), Index Buffer Objects (IBO).
- **GLSL Shaders**:
  - `vert.glsl`: 3D MVP matrix transformation, per-face directional ambient shading, texture coordinates.
  - `frag.glsl`: Texture array sampling with alpha testing (`discard` for transparent textures like plants/saplings).
- **Texture Arrays & Mipmaps**: 2D Texture Array (`GL_TEXTURE_2D_ARRAY`) packing 256 16×16 textures with nearest-neighbor magnification and mipmap generation.
- **Dynamic Chunking & Face Culling**:
  - 16×128×16 chunk columns partitioned into 4×4×4 subchunks.
  - Adjacent face culling (opaque and glass face culling) to only render visible block faces.
  - Subchunk mesh re-generation on block modification for instant updates.
- **Raycasting**:
  - DDA 3D grid raymarching for block picking, breaking, and placing.
- **Physics & Collision Detection**:
  - Continuous Swept AABB (Axis-Aligned Bounding Box) collision detection with normal reflection.
  - Variable speed movement (walking 4.317 m/s, sprinting 7 m/s), jumping (1.25m height), gravity (-32 m/s²), and ground friction / air drag.
  - Toggleable flying mode (`F`).
- **NBT Save & Load**:
  - World chunks serialized in Minecraft's NBT format using `nbtlib` and base-36 chunk hashing.

---

## Hardware Spec Tuning
- **Target Hardware**: Intel Core i5-13450HX | 16 GB DDR5 RAM | NVIDIA GeForce RTX 4050 GPU (6GB VRAM)
- **Render Distance**: Tuned to a 16-chunk sweet spot (4×4 chunk grid, 128 blocks high) delivering a smooth 60+ FPS without VRAM exhaustion.

---

## Controls

| Key / Mouse Action | Action |
| --- | --- |
| **Left Click (Window)** | Capture mouse & look around |
| **Escape** | Release mouse cursor |
| **Mouse Move** | Look around (yaw & pitch) |
| **W, A, S, D** | Move Forward, Left, Backward, Right |
| **Left Ctrl** | Sprint (Field of view expands dynamically) |
| **Space** | Jump (or Fly Up when flying) |
| **Left Shift** | Fly Down (when flying) |
| **F** | Toggle Flying Mode |
| **Left Click** | Mine / Break targeted block |
| **Right Click** | Place held block against targeted face |
| **Middle Click** | Pick block under crosshair |
| **G** | Randomize held block |
| **O** | Save modified chunks to disk (NBT) |
| **R** | Teleport to random spot on world surface |

---

## Requirements & Running

### Dependencies
- Python 3.10+ (tested on Python 3.11)
- `pyglet`
- `pyglm`
- `nbtlib`
- `base36`
- `numpy`

### Run Game
```bash
python main.py
```
