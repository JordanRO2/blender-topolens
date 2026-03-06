# Face Type Colors

Blender 5.0+ addon that highlights Tris, Quads, and Ngons with different colors in Edit Mode.

## Features

- GPU overlay with configurable colors and alpha per face type
- Toggle visibility for Tris (3), Quads (4), Ngons (5+)
- Normal offset (positive = in front, negative = behind faces)
- Face scale for plate-style visualization
- Live topology stats (count and percentage)
- No z-fighting (normal offset approach)
- Draws behind edges and vertices

## Installation

1. Download the latest release `.zip`
2. Blender > `Edit > Preferences > Add-ons > Install...` > select the `.zip`
3. Enable **"Face Type Colors"**

Or clone and copy the folder to your addons path:
```
%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons\
```

## Usage

1. Select a mesh object
2. Enter Edit Mode (`Tab`)
3. `View3D > Sidebar (N) > Topo Colors`
4. Enable **"Overlay Active"**

## Requirements

- Blender 5.0+
