# BLENDER_LOS_V2.py
# A Python code to make visibility analyses in Blender
# Designed by: I. Intxaurbe (https://github.com/inakiintxaurbe)
# Department of Graphic Design and Engineering Projects
# (Universidad del País Vasco / Euskal Herriko Unibertsitatea)
# PACEA UMR 5199
# (Université de Bordeaux)
# Date: 2026-04-04
#
# Copyright (C) 2026 Iñaki Intxaurbe
#
# Usage:
# It allows you to observe which points are visible and which are not
# from a pre-set camera in an environment (e.g., a cave with rock art),
# including optional horizontal head rotation (left-right),
# and automatic rendering of the simulated field of view.

import bpy
import bmesh
import csv
import math
import random
from mathutils import Vector, Matrix


# CONFIGURATION / EZARPENAK ------------------------------------

PANEL_OBJECT_NAME = "Target_Panel"

POINT_DENSITY_CM = 3.0
H_FOV_DEG = 60.0
V_FOV_DEG = 40.0
MAX_DISTANCE_M = 50.0

USE_HEAD_ROTATION = True
HEAD_YAW_ANGLES_DEG = [0, -45, -30, -15, 15, 30, 45]

DO_RENDER = True
RENDER_ENGINE = 'BLENDER_EEVEE_NEXT' 
RENDER_RES_X = 1600
RENDER_RES_Y = 1000
RENDER_FILE_FORMAT = 'PNG'

COLOR_VISIBLE_ORTHO = (0.1, 0.8, 0.1, 1.0)   
COLOR_VISIBLE_YAW   = (0.5, 1.0, 0.5, 1.0)   
COLOR_HIDDEN        = (0.8, 0.1, 0.1, 1.0)   
COLOR_OUTSIDE       = (0.5, 0.5, 0.5, 1.0)   

scene = bpy.context.scene
camera = scene.camera
panel = bpy.data.objects.get(PANEL_OBJECT_NAME)

depsgraph = bpy.context.evaluated_depsgraph_get()
mesh = panel.data

origin = camera.matrix_world.translation
cam_rot = camera.matrix_world.to_quaternion()

cam_forward = (cam_rot @ Vector((0, 0, -1))).normalized()
cam_right   = (cam_rot @ Vector((1, 0, 0))).normalized()
cam_up      = (cam_rot @ Vector((0, 1, 0))).normalized()

h_fov = math.radians(H_FOV_DEG) / 2.0
v_fov = math.radians(V_FOV_DEG) / 2.0

output_dir = bpy.path.abspath("//")
csv_path = output_dir + "panel_visibility.csv"


# FUNCTIONS / FUNTZIOAK -----------------------------------

def point_in_fov(dir_norm, forward, right, up, h_fov_rad, v_fov_rad):
    """
    Checks whether a normalized direction vector falls inside
    a rectangular horizontal/vertical field of view.
    """
    x = dir_norm.dot(right)
    y = dir_norm.dot(up)
    z = dir_norm.dot(forward)

    if z <= 0:
        return False

    h_angle = math.atan2(x, z)
    v_angle = math.atan2(y, z)

    return (abs(h_angle) <= h_fov_rad) and (abs(v_angle) <= v_fov_rad)


def rotated_head_vectors(base_forward, base_right, base_up, yaw_deg):
    """
    Rotates head direction left-right (yaw) around the local up axis.
    """
    yaw_rad = math.radians(yaw_deg)
    rot = Matrix.Rotation(yaw_rad, 3, base_up)

    new_forward = (rot @ base_forward).normalized()
    new_right = (rot @ base_right).normalized()
    new_up = base_up.normalized()

    return new_forward, new_right, new_up


def make_material(name, color):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)

    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError(f'Could not find "Principled BSDF" node in material "{name}".')

    bsdf.inputs["Base Color"].default_value = color
    return mat


def configure_render(camera_obj, h_fov_deg, res_x, res_y, file_format='PNG', engine='BLENDER_EEVEE'):
    """
    Configures scene render settings and camera FOV.
    Important: Blender camera stores one FOV; the apparent vertical FOV
    depends on image aspect ratio. Use a coherent resolution.
    """
    scene = bpy.context.scene
    cam_data = camera_obj.data

    scene.camera = camera_obj
    scene.render.engine = engine
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = file_format

    cam_data.lens_unit = 'FOV'
    cam_data.angle = math.radians(h_fov_deg)


def render_current_view(filepath):
    """
    Renders current camera view to file.
    """
    scene = bpy.context.scene
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)


def render_camera_pose(camera_obj, filepath, yaw_deg=0):
    original_rot_mode = camera_obj.rotation_mode
    original_rotation = camera_obj.rotation_euler.copy()
    original_location = camera_obj.location.copy()

    camera_obj.rotation_mode = 'XYZ'

    camera_obj.rotation_euler = original_rotation.copy()
    camera_obj.rotation_euler.z += math.radians(yaw_deg)

    bpy.context.view_layer.update()
    render_current_view(filepath)

    camera_obj.location = original_location
    camera_obj.rotation_euler = original_rotation
    camera_obj.rotation_mode = original_rot_mode
    bpy.context.view_layer.update()


# RENDERS / RENDERRAK -------------------------------------

configure_render(
        camera,
        H_FOV_DEG,
        RENDER_RES_X,
        RENDER_RES_Y,
        file_format=RENDER_FILE_FORMAT,
        engine=RENDER_ENGINE
    )

ortho_render_path = output_dir + "render_orthogonal.png"
render_camera_pose(camera, ortho_render_path, yaw_deg=0)

for yaw in HEAD_YAW_ANGLES_DEG:
    if yaw == 0: 
        continue        
    render_path = output_dir + f"render_yaw_{yaw:+03d}.png"
    render_camera_pose(camera, render_path, yaw_deg=yaw)

print("Rendered images saved to:")
print(f" - {output_dir}render_orthogonal.png")
for yaw in HEAD_YAW_ANGLES_DEG:
    if yaw == 0:
        continue
    print(f" - {output_dir}render_yaw_{yaw:+03d}.png")

# COLOURS (MATERIALS) / KOLOREAK (MATERIALAK) ---------------

mat_visible_ortho = make_material("VISIBLE_ORTHO", COLOR_VISIBLE_ORTHO)
mat_visible_yaw   = make_material("VISIBLE_YAW", COLOR_VISIBLE_YAW)
mat_hidden        = make_material("NOT_VISIBLE", COLOR_HIDDEN)
mat_outside       = make_material("OUTSIDE", COLOR_OUTSIDE)

panel.data.materials.clear()
panel.data.materials.append(mat_visible_ortho)  
panel.data.materials.append(mat_visible_yaw)    
panel.data.materials.append(mat_hidden)         
panel.data.materials.append(mat_outside)        


# VISIBILITY ANALYSIS / IKUSGARRITASUN ANALISIA -------------

bm = bmesh.new()
bm.from_mesh(mesh)

points = []
density_m = POINT_DENSITY_CM / 100.0

for face in bm.faces:
    if len(face.verts) < 3:
        continue

    area = face.calc_area()
    n_points = max(1, int(area / (density_m ** 2)))

    for _ in range(n_points):
        # Simplified sampling using the first triangle of the face
        # For quads/ngons, triangulating the mesh beforehand would be more robust
        u = math.sqrt(random.random())
        v = random.random()

        if u + v > 1:
            u = 1 - u
            v = 1 - v

        w = 1 - u - v

        v0, v1, v2 = face.verts[:3]
        point = (v0.co * u) + (v1.co * v) + (v2.co * w)
        points.append((point, face.index))

bm.free()


results = []
yaw_list = HEAD_YAW_ANGLES_DEG if USE_HEAD_ROTATION else [0]

for idx, (local_point, face_index) in enumerate(points):
    world_point = panel.matrix_world @ local_point
    direction = world_point - origin
    distance = direction.length

    visible_in_any_pose = False
    visible_pose = None
    status = "UNDEFINED"
    mat_index = 2

    if distance > MAX_DISTANCE_M:
        status = "OUTSIDE_RANGE"
        mat_index = 3
    else:
        dir_norm = direction.normalized()

        for yaw in yaw_list:
            head_forward, head_right, head_up = rotated_head_vectors(
                cam_forward, cam_right, cam_up, yaw
            )

            inside_fov = point_in_fov(
                dir_norm,
                head_forward,
                head_right,
                head_up,
                h_fov,
                v_fov
            )

            if not inside_fov:
                continue

            hit, loc, normal, face_hit_index, obj, matrix = scene.ray_cast(
                depsgraph,
                origin,
                dir_norm,
                distance=distance - 0.01
            )

            if hit and obj != panel:
                continue

            visible_in_any_pose = True
            visible_pose = yaw
            break

        if visible_in_any_pose:
            if visible_pose == 0:
                status = "VISIBLE_ORTHOGONAL"
                mat_index = 0
            else:
                status = f"VISIBLE_WITH_YAW_{visible_pose}"
                mat_index = 1
        else:
            status = "BLOCKED_OR_OUTSIDE_FOV"
            mat_index = 2

    results.append({
        "id": idx,
        "face_index": face_index,
        "x": world_point.x,
        "y": world_point.y,
        "z": world_point.z,
        "distance_m": distance,
        "status": status,
        "visible_yaw_deg": visible_pose,
        "mat_index": mat_index
    })


face_best_mat = {}

material_priority = {
    0: 0,  
    1: 1,  
    2: 2,  
    3: 3   
}

for r in results:
    fi = r["face_index"]
    mat = r["mat_index"]

    if fi not in face_best_mat:
        face_best_mat[fi] = mat
    else:
        current_mat = face_best_mat[fi]

        if material_priority[mat] < material_priority[current_mat]:
            face_best_mat[fi] = mat

for poly in panel.data.polygons:
    poly.material_index = 2
    
for fi, mat in face_best_mat.items():
    if fi < len(panel.data.polygons):
        panel.data.polygons[fi].material_index = mat
        
if results:
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
