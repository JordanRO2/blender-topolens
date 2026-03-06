"""
Face Type Colors — Addon para Blender 5.0+
============================================
Muestra colores diferentes para Tris, Quads y Ngons en Edit Mode.
Overlay configurable con colores y opacidad personalizables.

Panel en: View3D > Sidebar (N) > pestaña "Topo Colors"
"""

bl_info = {
    "name": "Face Type Colors",
    "author": "JordanRO2",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Topo Colors",
    "description": "Colorea Tris, Quads y Ngons con colores diferentes en Edit Mode",
    "category": "Mesh",
}

import bpy
from . import overlay


def register():
    overlay.register()


def unregister():
    overlay.unregister()


if __name__ == "__main__":
    register()
