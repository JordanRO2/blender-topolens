"""
Face Type Colors — GPU overlay for Tris, Quads, and Ngons.
Z-fighting fixed by offsetting vertices along face normals.
"""

import bpy
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.props import (
    FloatVectorProperty,
    FloatProperty,
    BoolProperty,
)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

class FaceTypeColorsProperties(bpy.types.PropertyGroup):
    enabled: BoolProperty(
        name="Enable",
        description="Toggle face type color overlay",
        default=False,
        update=lambda self, ctx: _toggle_overlay(self, ctx),
    )
    tri_color: FloatVectorProperty(
        name="Tris",
        description="Color for triangles (3 vertices)",
        subtype='COLOR_GAMMA',
        default=(0.8, 0.2, 0.8, 0.4),
        min=0.0, max=1.0,
        size=4,
    )
    quad_color: FloatVectorProperty(
        name="Quads",
        description="Color for quads (4 vertices)",
        subtype='COLOR_GAMMA',
        default=(1.0, 0.6, 0.0, 0.4),
        min=0.0, max=1.0,
        size=4,
    )
    ngon_color: FloatVectorProperty(
        name="Ngons",
        description="Color for ngons (5+ vertices)",
        subtype='COLOR_GAMMA',
        default=(0.9, 0.1, 0.1, 0.4),
        min=0.0, max=1.0,
        size=4,
    )
    show_tris: BoolProperty(name="Tris", default=True)
    show_quads: BoolProperty(name="Quads", default=True)
    show_ngons: BoolProperty(name="Ngons", default=True)
    normal_offset: FloatProperty(
        name="Offset",
        description="Normal offset (positive = in front, negative = behind faces)",
        default=0.005,
        min=-0.1, max=0.1,
    )
    face_scale: FloatProperty(
        name="Scale",
        description="Face scale (1.0 = full face, 0.5 = half size plate)",
        default=1.0,
        min=0.01, max=1.0,
    )


# ---------------------------------------------------------------------------
# Draw handler
# ---------------------------------------------------------------------------

_draw_handle = None


def _toggle_overlay(self, context):
    global _draw_handle
    if self.enabled:
        if _draw_handle is None:
            _draw_handle = bpy.types.SpaceView3D.draw_handler_add(
                _draw_callback, (context,), 'WINDOW', 'POST_VIEW'
            )
    else:
        if _draw_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
            _draw_handle = None
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


def _draw_callback(context):
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return
    if context.mode != 'EDIT_MESH':
        return

    props = context.scene.face_type_colors
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    bm.faces.ensure_lookup_table()

    if not bm.faces:
        return

    mat = obj.matrix_world
    offset = props.normal_offset

    all_coords = []
    all_colors = []

    tri_col = tuple(props.tri_color)
    quad_col = tuple(props.quad_color)
    ngon_col = tuple(props.ngon_color)

    for face in bm.faces:
        nv = len(face.verts)

        if nv == 3 and props.show_tris:
            color = tri_col
        elif nv == 4 and props.show_quads:
            color = quad_col
        elif nv >= 5 and props.show_ngons:
            color = ngon_col
        else:
            continue

        # Shrink toward face center + offset along normal
        normal = face.normal
        scale = props.face_scale
        if scale < 1.0:
            center = face.calc_center_median()
            verts = [mat @ (center + (v.co - center) * scale + normal * offset) for v in face.verts]
        else:
            verts = [mat @ (v.co + normal * offset) for v in face.verts]

        # Fan triangulation
        for i in range(1, len(verts) - 1):
            all_coords.append(verts[0])
            all_coords.append(verts[i])
            all_coords.append(verts[i + 1])
            all_colors.append(color)
            all_colors.append(color)
            all_colors.append(color)

    if not all_coords:
        return

    shader = gpu.shader.from_builtin('SMOOTH_COLOR')

    gpu.state.blend_set('ALPHA')
    gpu.state.face_culling_set('NONE')
    # depth_mask=False: overlay won't write to depth buffer,
    # so edges and vertices (drawn later) always appear on top
    gpu.state.depth_mask_set(False)
    gpu.state.depth_test_set('LESS_EQUAL')

    batch = batch_for_shader(shader, 'TRIS', {
        "pos": all_coords,
        "color": all_colors,
    })
    shader.bind()
    batch.draw(shader)

    gpu.state.depth_mask_set(True)
    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set('NONE')
    gpu.state.face_culling_set('NONE')


# ---------------------------------------------------------------------------
# Timer for continuous redraw in edit mode
# ---------------------------------------------------------------------------

_timer_handle = None


def _timer_redraw():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    return 0.1


def _start_timer():
    global _timer_handle
    if _timer_handle is None:
        _timer_handle = bpy.app.timers.register(_timer_redraw, persistent=True)


def _stop_timer():
    global _timer_handle
    if _timer_handle is not None:
        try:
            bpy.app.timers.unregister(_timer_redraw)
        except ValueError:
            pass
        _timer_handle = None


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------

class VIEW3D_PT_face_type_colors(bpy.types.Panel):
    bl_label = "Face Type Colors"
    bl_idname = "VIEW3D_PT_face_type_colors"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Topo Colors"

    def draw(self, context):
        layout = self.layout
        props = context.scene.face_type_colors

        row = layout.row()
        row.scale_y = 1.5
        icon = 'HIDE_OFF' if props.enabled else 'HIDE_ON'
        row.prop(props, "enabled", text="Overlay Active", icon=icon, toggle=True)

        if not props.enabled:
            return

        layout.separator()

        box = layout.box()
        box.label(text="Colors", icon='COLOR')

        row = box.row(align=True)
        row.prop(props, "show_tris", text="", toggle=True)
        row.prop(props, "tri_color", text="Tris (3)")

        row = box.row(align=True)
        row.prop(props, "show_quads", text="", toggle=True)
        row.prop(props, "quad_color", text="Quads (4)")

        row = box.row(align=True)
        row.prop(props, "show_ngons", text="", toggle=True)
        row.prop(props, "ngon_color", text="Ngons (5+)")

        layout.separator()
        layout.prop(props, "normal_offset", slider=True)
        layout.prop(props, "face_scale", slider=True)

        # Stats
        obj = context.active_object
        if obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(obj.data)
            tris = sum(1 for f in bm.faces if len(f.verts) == 3)
            quads = sum(1 for f in bm.faces if len(f.verts) == 4)
            ngons = sum(1 for f in bm.faces if len(f.verts) >= 5)
            total = len(bm.faces)

            box = layout.box()
            box.label(text="Topology", icon='MESH_DATA')
            col = box.column(align=True)
            col.label(text=f"Total: {total}")
            col.label(text=f"Tris: {tris}  ({100*tris/max(1,total):.0f}%)")
            col.label(text=f"Quads: {quads}  ({100*quads/max(1,total):.0f}%)")
            col.label(text=f"Ngons: {ngons}  ({100*ngons/max(1,total):.0f}%)")
        elif context.mode != 'EDIT_MESH':
            box = layout.box()
            box.label(text="Enter Edit Mode (Tab)", icon='INFO')


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    FaceTypeColorsProperties,
    VIEW3D_PT_face_type_colors,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.face_type_colors = bpy.props.PointerProperty(type=FaceTypeColorsProperties)
    _start_timer()


def unregister():
    global _draw_handle
    _stop_timer()
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None
    del bpy.types.Scene.face_type_colors
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
