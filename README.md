# 3D Minecraft Clone in Python

A feature-complete 3D Minecraft Alpha clone implemented in Python using Modern OpenGL 3.3 Core Profile. Built step-by-step strictly following the low-level graphics pipeline architecture from the reference tutorial series by obiwac.

---

## Overview

This project is a standalone voxel engine and 3D sandbox game replicating core Minecraft Alpha mechanics: procedural block rendering, dynamic chunking, face culling, continuous AABB physics, raycast block modification, and NBT-based world persistence.

---

## Tech Stack & Architecture

| Component | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.11 | Core gameplay logic, world generation, and math |
| **Window & Input** | `pyglet` (2.x) | Cross-platform windowing, OpenGL 3.3 Core context, audio, and event loop |
| **Graphics API** | OpenGL 3.3 Core Profile (GLSL) | Hardware-accelerated 3D rendering pipeline |
| **Mathematics** | Custom Matrix engine / `pyglm` | Perspective projections, model-view transformations, vector math |
| **Data Storage** | `nbtlib` & `base36` | Minecraft Named Binary Tag (NBT) chunk serialization and directory hashing |
| **Arrays & Buffers** | `ctypes` & `numpy` | Low-level C-compatible memory buffers for VAO / VBO / IBO GPU transfer |

---

## Key Engineering Features

- **Modern OpenGL Pipeline**:
  - Programmable shaders: `vert.glsl` (MVP transform, per-face directional ambient shading) and `frag.glsl` (2D texture array sampling, alpha discard for transparent foliage).
  - High-performance 2D Texture Array (`GL_TEXTURE_2D_ARRAY`) bundling 256 16×16 textures into a single GPU binding with nearest-neighbor filtering and mipmapping.
- **Dynamic Chunking & Face Culling**:
  - Full-height chunk columns (16×128×16) partitioned into 4×4×4 subchunks for localized, zero-lag mesh updates.
  - Hidden-surface culling: adjacent solid block faces and shared glass/liquid faces are discarded to minimize GPU draw calls.
  - Dual-sided inward liquid rendering so water bodies remain visible both from surface view and while submerged.
- **Raycast Block Interaction**:
  - 3D DDA grid traversal raymarching for voxel selection, mining, and surface-aligned placement.
- **Continuous Physics & Collisions**:
  - Swept Axis-Aligned Bounding Box (AABB) collision resolution with surface normal reflection.
  - Variable player movement states: walking (4.3 m/s), sprinting (7.0 m/s), jumping (1.25 m), gravity (-32 m/s²), water buoyancy/drag, and toggleable flight.
  - Void fall protection: automatic safe respawn if falling off world boundaries.
- **In-Game Hotbar & Inventory**:
  - 9-slot interactive hotbar with instant numeric switching (keys `1`–`9`), mouse wheel cycling, and middle-click block picking.
  - Broken block drops and inventory count tracking with on-screen HUD toast notifications.
- **World Persistence**:
  - Gzipped Minecraft NBT region chunk files (`c.x.z.dat`) with progressive streaming.

---

## Controls

| Input | Action |
|---|---|
| **Left Click (Window)** | Capture mouse & look around |
| **Escape** | Release mouse cursor |
| **Mouse Move** | Pitch & Yaw look rotation |
| **W, A, S, D** | Move Forward, Left, Backward, Right |
| **Left Ctrl** | Sprint (dynamic FOV zoom) |
| **Space** | Jump (or Swim Up in water / Fly Up in flight mode) |
| **Left Shift** | Fly Down (while in flight mode) |
| **F** | Toggle Flying Mode on/off |
| **1 – 9** | Select Hotbar Slots 1 through 9 |
| **Mouse Scroll** | Cycle through Hotbar blocks |
| **Left Click** | Mine / Break targeted block (collects into inventory) |
| **Right Click** | Place held block on targeted surface |
| **Middle Click** | Pick targeted block into active hotbar slot |
| **G** | Randomize held block |
| **O** | Save modified chunks to disk (NBT) |
| **R** | Teleport to a random surface location |

---

## Getting Started

### 1. Prerequisites
Ensure Python 3.10+ is installed on your machine.

### 2. Install Dependencies
```bash
pip install pyglet pyglm nbtlib base36 numpy
```

### 3. Run the Game
```bash
python main.py
```
