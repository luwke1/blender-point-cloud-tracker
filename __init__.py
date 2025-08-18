import bpy
import os
import subprocess

bl_info = {
    "name": "Point Cloud Camera Tracker",
    "author": "Luke Flock",
    "version": (3, 7),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Point Cloud Camera Tracker",
    "description": "Generates a point cloud from a video to create a nice camera track.",
    "category": "Object",
}


def is_addon_enabled(module_name):
    """Checks if a Blender add-on is enabled."""
    return module_name in bpy.context.preferences.addons


# -------------------------------------------------------------------
# PROPERTIES
# -------------------------------------------------------------------

class PcloudTrackToolProperties(bpy.types.PropertyGroup):
    video_path: bpy.props.StringProperty(
        name="Video File",
        description="Select the video file for processing",
        subtype="FILE_PATH",
    )
    resolution_scale: bpy.props.FloatProperty(
        name="Max Image Size",
        description="Maximum size (width or height) of the extracted frames. Lower is faster",
        min=240, max=7680, default=1920,
    )
    num_features: bpy.props.IntProperty(
        name="Max Features Per Frame",
        description="Maximum number of features to extract per frame",
        min=1000, max=10000, default=5000,
    )
    match_overlap: bpy.props.IntProperty(
        name="Frame Overlap",
        description="Number of subsequent frames to match against",
        min=5, max=100, default=10,
    )
    auto_import: bpy.props.BoolProperty(
        name="Auto-Import When Done",
        description="Automatically import the point cloud after processing is complete. You must leave the console window open for this to work",
        default=True
    )
    last_output_path: bpy.props.StringProperty(
        name="Last Output Path",
        description="Path to the most recently generated point cloud's sparse folder",
        default=""
    )


# -------------------------------------------------------------------
# THE UI PANEL
# -------------------------------------------------------------------

class VIEW3D_PT_TrackToolPanel(bpy.types.Panel):
    bl_label = "Point Cloud Tracking"
    bl_idname = "VIEW3D_PT_video_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PCloud Camera Tracker"

    def draw(self, context):
        layout = self.layout
        props = context.scene.pcloud_track_tool_props

        # --- Section 1: Video Input ---
        box = layout.box()
        box.label(text="1. Video Input", icon='CAMERA_DATA')
        box.prop(props, "video_path")
        
         # --- Section 2: Point Cloud Settings ---
        box = layout.box()
        box.label(text="2. Point Cloud Settings", icon='SETTINGS')
        box.prop(props, "resolution_scale")
        box.prop(props, "num_features")
        box.prop(props, "match_overlap")

        # --- Section 3: Processing ---
        box = layout.box()
        box.label(text="2. Processing", icon='PLAY')
        box.prop(props, "auto_import")
        box.operator("pcloud_track_tool.generate_colmap", text="Generate Point Cloud", icon='CAMERA_DATA')

        # --- Section 4: Manual Import ---
        box = layout.box()
        box.label(text="3. Manual Import", icon='IMPORT')
        col = box.column(align=True)

        row = col.row()
        row.scale_y = 1.5

        # Check if the path is valid and convert to boolean
        is_valid_path = props.last_output_path and os.path.exists(props.last_output_path)
        row.enabled = bool(is_valid_path)
        row.operator("pcloud_track_tool.import_last_result", text="Import Last Result", icon='CUBE')

        row = col.row() 
        row.operator("pcloud_track_tool.import_custom_folder", text="Import from Folder...", icon='FILE_FOLDER')


# -------------------------------------------------------------------
# THE OPERATORS
# -------------------------------------------------------------------

class PCLOUD_TRACK_TOOL_OT_import_last_result(bpy.types.Operator):
    bl_idname = "pcloud_track_tool.import_last_result"
    bl_label = "Import Last COLMAP Result"
    bl_description = "Import the most recently generated point cloud"

    def execute(self, context):
        props = context.scene.pcloud_track_tool_props
        importer_addon_name = "photogrammetry_importer"

        if not props.last_output_path or not os.path.exists(props.last_output_path):
            self.report({'ERROR'}, "No valid output path found. Generate a point cloud first.")
            return {'CANCELLED'}

        if not is_addon_enabled(importer_addon_name):
            self.report({'ERROR'}, f"Please enable the '{importer_addon_name}' add-on.")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Importing from: {props.last_output_path}")
        try:
            bpy.ops.import_scene.colmap_model(directory=props.last_output_path)
            
        except Exception as e:
            self.report({'ERROR'}, f"Import failed. Ensure the COLMAP files exist. Error: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

class PCLOUD_TRACK_TOOL_OT_import_custom_folder(bpy.types.Operator):
    bl_idname = "pcloud_track_tool.import_custom_folder"
    bl_label = "Import Custom COLMAP Folder"
    bl_description = "Select a COLMAP sparse folder to import"
    
    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        importer_addon_name = "photogrammetry_importer"
        if not is_addon_enabled(importer_addon_name):
            self.report({'ERROR'}, f"Please enable the '{importer_addon_name}' add-on.")
            return {'CANCELLED'}
            
        import_path = self.directory
        if not import_path or not os.path.isdir(import_path):
            self.report({'ERROR'}, "A valid folder was not selected.")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Importing from custom path: {import_path}")
        try:
            bpy.ops.import_scene.colmap_model(directory=import_path)
        except Exception as e:
            self.report({'ERROR'}, f"Import failed. Error: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

class PCLOUD_TRACK_TOOL_OT_generate_colmap(bpy.types.Operator):
    bl_idname = "pcloud_track_tool.generate_colmap"
    bl_label = "Generate Point Cloud"
    bl_options = {'REGISTER', 'UNDO'}

    process = None

    def _extract_frames(self, context, video_path, output_dir):
        """Extracts frames from a video using Blender's VSE."""
        self.report({'INFO'}, "Extracting frames...")
        
        original_scene = context.window.scene
        temp_scene = bpy.data.scenes.new(name="Frame Extraction Scene")
        context.window.scene = temp_scene
        
        try:
            temp_scene.render.image_settings.file_format = 'JPEG'
            temp_scene.render.image_settings.quality = 90
            temp_scene.render.filepath = os.path.join(output_dir, "frame_")
            
            temp_scene.sequence_editor_create()
            strip = temp_scene.sequence_editor.sequences.new_movie(
                name="video_strip", filepath=video_path, channel=1, frame_start=1)
            
            temp_scene.frame_start = 1
            temp_scene.frame_end = strip.frame_final_duration
            
            bpy.ops.render.render(animation=True, write_still=True, scene=temp_scene.name)

        except Exception as e:
            self.report({'ERROR'}, f"Frame extraction failed: {e}")
            return False
        finally:
            context.window.scene = original_scene
            bpy.data.scenes.remove(temp_scene)
            
        self.report({'INFO'}, "Frame extraction complete.")
        return True

    def execute(self, context):
        props = context.scene.pcloud_track_tool_props
        addon_dir = os.path.dirname(os.path.abspath(__file__))

        # --- 1. Define all paths ---
        colmap_exe_path = os.path.normpath(os.path.join(addon_dir, 'bin', 'win64', 'COLMAP', 'bin', 'colmap.exe'))
        batch_script_path = os.path.normpath(os.path.join(addon_dir, 'process.bat'))
        video_path = bpy.path.abspath(props.video_path)
        
        # --- 2. Validate paths and settings ---
        if not os.path.exists(colmap_exe_path):
            self.report({'ERROR'}, f"colmap.exe not found at: {colmap_exe_path}")
            return {'CANCELLED'}
        if not os.path.exists(batch_script_path):
            self.report({'ERROR'}, f"Required script not found: {batch_script_path}")
            return {'CANCELLED'}
        if not video_path or not os.path.exists(video_path):
            self.report({'ERROR'}, "Please select a valid video file.")
            return {'CANCELLED'}

        # --- 3. Create directory structure ---
        video_filename = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(os.path.dirname(video_path), "colmap_output", video_filename)
        images_dir = os.path.join(output_dir, "images")
        sparse_dir = os.path.join(output_dir, "sparse")
        database_path = os.path.join(output_dir, 'database.db')

        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(sparse_dir, exist_ok=True)
        
        props.last_output_path = sparse_dir

        # --- 4. Extract frames from the video ---
        if not self._extract_frames(context, video_path, images_dir):
            return {'CANCELLED'}

        # --- 5. Prepare the list of arguments for the batch script ---
        command_args = [
            batch_script_path,
            colmap_exe_path,
            database_path,
            images_dir,
            sparse_dir,
            str(int(props.resolution_scale)),
            str(props.match_overlap),
            str(props.num_features),
            video_filename
        ]
        
        self.report({'INFO'}, "Starting COLMAP process. See console for progress.")

        # --- 6. Execute the script with the arguments ---
        try:
            self.process = subprocess.Popen(command_args, creationflags=subprocess.CREATE_NEW_CONSOLE)
            if props.auto_import:
                bpy.app.timers.register(lambda: self.check_process_and_import(context))
        except Exception as e:
            self.report({'ERROR'}, f"Failed to start batch process: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}
    
    def check_process_and_import(self, context):
        """Timer function to check if the COLMAP process has finished."""
        if self.process and self.process.poll() is not None:
            self.report({'INFO'}, "COLMAP process finished. Importing results.")
            bpy.ops.pcloud_track_tool.import_last_result()
            self.process = None
            return None
        
        return 0.5

# -------------------------------------------------------------------
# REGISTRATION
# -------------------------------------------------------------------
classes = (
    PcloudTrackToolProperties,
    VIEW3D_PT_TrackToolPanel,
    PCLOUD_TRACK_TOOL_OT_import_last_result,
    PCLOUD_TRACK_TOOL_OT_import_custom_folder,
    PCLOUD_TRACK_TOOL_OT_generate_colmap,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.pcloud_track_tool_props = bpy.props.PointerProperty(type=PcloudTrackToolProperties)

def unregister():
    del bpy.types.Scene.pcloud_track_tool_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()