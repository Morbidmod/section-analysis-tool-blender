import bpy
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty
from bpy.types import Operator, Panel, PropertyGroup

bl_info = {
    "name": "Section Analysis Tool",
    "author": "Morbidmod",
    "version": (1, 7),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Section Analysis",
    "description": "Fusion 360-style section analysis tool",
    "category": "3D View",
}

class SectionAnalysisSettings(PropertyGroup):
    cut_distance: FloatProperty(
        name="Distance",
        default=0.0,
        description="Distance from origin"
    )
    
    cut_axis: EnumProperty(
        name="Axis",
        items=[
            ('X', 'X-Axis', 'X Axis'),
            ('Y', 'Y-Axis', 'Y Axis'),
            ('Z', 'Z-Axis', 'Z Axis')
        ],
        default='Z',
        description="Cut plane axis"
    )
    
    cut_rotation: FloatProperty(
        name="Tilt",
        default=0.0,
        description="Tilts the cutting plane's face toward or away from the object, in degrees"
    )
    
    show_wireframe: BoolProperty(
        name="Show Wireframe",
        default=True,
        description="Display cutting plane as wireframe"
    )

    plane_size_mode: EnumProperty(
        name="Size Mode",
        items=[
            ('MANUAL', 'Manual', 'Use a fixed cutting plane size'),
            ('AUTO', 'Auto (Selection)', "Size the plane to fit the selected objects' combined bounding box")
        ],
        default='AUTO',
        description="How the cutting plane size is determined"
    )

    plane_size: FloatProperty(
        name="Plane Size",
        default=20.0,
        min=0.01,
        description="Size of the cutting plane, used when Size Mode is Manual"
    )

    plane_size_margin: FloatProperty(
        name="Margin",
        default=1.2,
        min=1.0,
        description="Multiplier applied to the selection's bounding box so the plane extends past the geometry, used when Size Mode is Auto"
    )

    center_on_selection: BoolProperty(
        name="Center on Selection",
        default=True,
        description="Position the cutting plane at the center of the selected objects' bounding box, instead of world origin, before offsetting by Distance"
    )

def get_selection_bounds(objects):
    """Return (min_corner, max_corner) world-space Vectors for the combined
    bounding box of the given mesh objects, or None if none have geometry."""
    corners = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        for corner in obj.bound_box:
            corners.append(obj.matrix_world @ Vector(corner))

    if not corners:
        return None

    min_corner = Vector((
        min(c.x for c in corners),
        min(c.y for c in corners),
        min(c.z for c in corners)
    ))
    max_corner = Vector((
        max(c.x for c in corners),
        max(c.y for c in corners),
        max(c.z for c in corners)
    ))
    return min_corner, max_corner


class VIEW3D_OT_section_analysis(Operator):
    bl_idname = "view3d.section_analysis"
    bl_label = "Section Analysis"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Check if objects are selected
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        # Get all mesh objects
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        settings = context.scene.section_analysis_settings

        # Combined world-space bounding box of the selection, used for
        # auto-sizing and/or centering below
        bounds = get_selection_bounds(mesh_objects)

        # Determine cutting plane size: either the manual value, or fit to
        # the combined bounding box of the selected mesh objects
        if settings.plane_size_mode == 'AUTO':
            if bounds:
                bbox_min, bbox_max = bounds
                diagonal = (bbox_max - bbox_min).length
                plane_size = diagonal * settings.plane_size_margin if diagonal > 0 else settings.plane_size
            else:
                plane_size = settings.plane_size
        else:
            plane_size = settings.plane_size

        # Determine base position: selection bounding box center, or world
        # origin, before the axis-aligned Distance offset is applied
        if settings.center_on_selection and bounds:
            bbox_min, bbox_max = bounds
            center = (bbox_min + bbox_max) / 2
        else:
            center = Vector((0.0, 0.0, 0.0))

        # Create a plane as cutting object
        bpy.ops.mesh.primitive_plane_add(
            size=plane_size,
            enter_editmode=False,
            align='WORLD',
            location=(0, 0, 0)
        )
        
        cutter = context.active_object
        cutter.name = "Section_Cutter"
        
        # Position and rotate the plane correctly for sectioning
        axis = settings.cut_axis
        distance = settings.cut_distance
        tilt = settings.cut_rotation

        # The plane is created flat, with its normal along Z. Reorient it so
        # its normal instead faces the chosen cut axis (Z needs no change).
        base_orientation = {
            'X': Matrix.Rotation(math.radians(90), 4, 'Y'),
            'Y': Matrix.Rotation(math.radians(-90), 4, 'X'),
            'Z': Matrix.Identity(4),
        }[axis]

        # Apply Tilt as a rotation around an axis lying IN the plane (i.e.
        # perpendicular to its normal), so it actually angles the cutting
        # face toward/away from the object. Rotating around the normal
        # itself (the old behavior) has no visible effect on a symmetric
        # plane other than spinning its square outline.
        tilt_axis = {'X': 'Y', 'Y': 'Z', 'Z': 'X'}[axis]
        tilt_rotation = Matrix.Rotation(math.radians(tilt), 4, tilt_axis)
        cutter.rotation_euler = (tilt_rotation @ base_orientation).to_euler()

        # Set position based on axis (base center, offset along the cut axis)
        if axis == 'X':
            cutter.location = (center.x + distance, center.y, center.z)
        elif axis == 'Y':
            cutter.location = (center.x, center.y + distance, center.z)
        else:  # Z
            cutter.location = (center.x, center.y, center.z + distance)
        
        # Add material to the cutter
        mat = bpy.data.materials.new(name="Cutter_Material")
        mat.use_nodes = True
        mat.node_tree.nodes.clear()
        
        output_node = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (300, 0)
        
        bsdf_node = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf_node.location = (0, 0)
        bsdf_node.inputs['Base Color'].default_value = (0.2, 0.6, 1.0, 0.3)  # Semi-transparent blue
        bsdf_node.inputs['Alpha'].default_value = 0.3
        
        mat.node_tree.links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
        
        cutter.data.materials.append(mat)
        
        # Set wireframe display
        if settings.show_wireframe:
            cutter.display_type = 'WIRE'
        else:
            cutter.display_type = 'SOLID'
        
        # Add boolean modifier to each mesh object
        for obj in mesh_objects:
            if obj != cutter:  # Don't add modifier to the cutter itself
                bool_mod = obj.modifiers.new(name="Section_Boolean", type='BOOLEAN')
                bool_mod.object = cutter
                bool_mod.operation = 'DIFFERENCE'
        
        self.report({'INFO'}, f"Section analysis applied to {len(mesh_objects)} objects")
        return {'FINISHED'}

class VIEW3D_OT_clear_section_analysis(Operator):
    bl_idname = "view3d.clear_section_analysis"
    bl_label = "Clear Section Analysis"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Find and remove the section cutter object
        cutter_objects = [obj for obj in bpy.data.objects if obj.name.startswith("Section_Cutter")]
        
        # Remove boolean modifiers from all objects
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                # Remove all boolean modifiers that reference our cutter
                for modifier in obj.modifiers:
                    if modifier.type == 'BOOLEAN' and modifier.object:
                        if modifier.object.name.startswith("Section_Cutter"):
                            obj.modifiers.remove(modifier)
        
        # Delete the cutter objects
        for cutter in cutter_objects:
            bpy.data.objects.remove(cutter, do_unlink=True)
        
        self.report({'INFO'}, "Section analysis cleared")
        return {'FINISHED'}

class VIEW3D_PT_section_analysis_panel(Panel):
    bl_label = "Section Analysis"
    bl_idname = "VIEW3D_PT_section_analysis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Section Analysis"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.section_analysis_settings
        
        row = layout.row()
        row.prop(settings, "cut_axis")
        
        row = layout.row()
        row.prop(settings, "cut_distance")
        
        row = layout.row()
        row.prop(settings, "cut_rotation")
        
        row = layout.row()
        row.prop(settings, "show_wireframe")

        row = layout.row()
        row.prop(settings, "center_on_selection")

        layout.separator()

        row = layout.row()
        row.prop(settings, "plane_size_mode")

        if settings.plane_size_mode == 'MANUAL':
            row = layout.row()
            row.prop(settings, "plane_size")
        else:
            row = layout.row()
            row.prop(settings, "plane_size_margin")
        
        layout.separator()
        
        row = layout.row()
        row.operator("view3d.section_analysis", text="Apply Section Analysis")
        
        row = layout.row()
        row.operator("view3d.clear_section_analysis", text="Clear Section Analysis")

classes = [
    SectionAnalysisSettings,
    VIEW3D_OT_section_analysis,
    VIEW3D_OT_clear_section_analysis,
    VIEW3D_PT_section_analysis_panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.section_analysis_settings = bpy.props.PointerProperty(
        type=SectionAnalysisSettings
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.section_analysis_settings

if __name__ == "__main__":
    register()
