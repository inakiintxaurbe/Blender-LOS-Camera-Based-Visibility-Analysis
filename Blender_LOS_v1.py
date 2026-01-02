# BLENDER_LOS_V1.py  (a Python code to make visibility analyses in Blender)
# Designed by: I. Intxaurbe (https://github.com/inakiintxaurbe)
#   Department of Graphic Design and Engineering Projects
#   (Universidad del País Vasco/Euskal Herriko Unibertsitatea)
#   PACEA UMR 5199
#   (Université du Bordeaux)
#   Date: 2026-01-02 
#
# Copyright (C) 2026  Iñaki Intxaurbe
# 
# Usage: It allows you to observe which points are visible and which are not 
# from a pre-set camera in an environment (e.g.,a cave with rock art).
#
# Required inputs (same filenames as original workflow):
#   XXX.blend  (a Blender project -any name will do-)
#   XXX.obj, stl, etc.  (3D model of an environment -any name will do-)
#   Target_Panel.obj, stl, etc.     (3D model of a target panel -NAMED AS "Target_Panel"!!!-)
#   Light           (a point of light in the project)
#   a Camera       (a pre-set camera -ideally, place it at the correct height-)



import bpy
import bmesh
import csv
import math
import random
from mathutils import Vector



# CONFIGURATION / EZARPENAK

PANEL_OBJECT_NAME = "Target_Panel"  # ← CHANGE THIS TO NAME AS "Target_Panel" / IZENA "Target_Panel" IZAN BEHAR DAU!!! (IMPORTANT!!!)
POINT_DENSITY_CM = 3.0          # approximate separation between points (cm) / puntuen arteko gutxi gorabeherako tartea (cm)
H_FOV_DEG = 110.0               # horizontal human visual field / giza ikuseremu horizontala
V_FOV_DEG = 90.0                # vertical human visual field / giza ikuseremu bertikala
MAX_DISTANCE_M = 50.0           # maximum analysis distance / aztertzeko gehienezko distantzia
COLOR_VISIBLE = (0.1, 0.8, 0.1, 1.0)
COLOR_HIDDEN = (0.8, 0.1, 0.1, 1.0)
COLOR_OUTSIDE = (0.5, 0.5, 0.5, 1.0)



# UTILITIES / ERABILGARRITASUNAK

scene = bpy.context.scene
camera = scene.camera
if camera is None:
    raise RuntimeError("There is no active camera in the scene!!!")

panel = bpy.data.objects.get(PANEL_OBJECT_NAME)
if panel is None or panel.type != 'MESH':
    raise RuntimeError("The panel does not exist or is not a mesh!!! (OR ITS NOT NAMED AS "Target_Panel"!!!)")

depsgraph = bpy.context.evaluated_depsgraph_get()
panel_eval = panel.evaluated_get(depsgraph)
mesh = panel_eval.to_mesh()

origin = camera.matrix_world.translation
cam_forward = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))

h_fov = math.radians(H_FOV_DEG) / 2
v_fov = math.radians(V_FOV_DEG) / 2

output_dir = bpy.path.abspath("//")
csv_path = output_dir + "panel_visibility.csv"



# COLORING MATERIALS RESULTS / EMAITZAK KOLOREZTATZEKO MATERIALA

def make_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    return mat

mat_visible = make_material("VISIBLE", COLOR_VISIBLE)
mat_hidden = make_material("NO_VISIBLE", COLOR_HIDDEN)
mat_outside = make_material("FUERA_CAMPO", COLOR_OUTSIDE)

panel.data.materials.clear()
panel.data.materials.append(mat_visible)
panel.data.materials.append(mat_hidden)
panel.data.materials.append(mat_outside)



# SANPLING BY DENSITY / DENTSITATEAGAZ LAGINKETA

bm = bmesh.new()
bm.from_mesh(mesh)

points = []
density_m = POINT_DENSITY_CM / 100.0

for face in bm.faces:
    area = face.calc_area()
    n_points = max(1, int(area / (density_m ** 2)))

    for _ in range(n_points):
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



# VISIBILITY ANALYSIS / IKUSGARRITASUN ANALISIA

results = []

for idx, (local_point, face_index) in enumerate(points):
    world_point = panel.matrix_world @ local_point
    direction = world_point - origin
    distance = direction.length

    if distance > MAX_DISTANCE_M:
        status = "OUTSIDE_RANGE"
        mat_index = 2
    else:
        dir_norm = direction.normalized()
        angle = cam_forward.angle(dir_norm)

        if abs(angle) > h_fov:
            status = "OUTSIDE_FOV"
            mat_index = 2
        else:
            hit, loc, _, _, obj, _ = scene.ray_cast(
                depsgraph,
                origin,
                dir_norm,
                distance=distance - 0.01
            )

            if hit and obj != panel:
                status = "BLOCKED"
                mat_index = 1
            else:
                status = "VISIBLE"
                mat_index = 0

    results.append({
    "id": idx,
    "face_index": face_index,
    "x": world_point.x,
    "y": world_point.y,
    "z": world_point.z,
    "distance_m": distance,
    "status": status,
    "mat_index": mat_index
})



# SAVE RESULTS IN CSV / CSV-AN GORDE EMAITZAK

for r in results:
    fi = r["face_index"]
    if fi < len(panel.data.polygons):
        panel.data.polygons[fi].material_index = r["mat_index"]
        
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

panel_eval.to_mesh_clear()

print("Análisis completado.")
print(f"Resultados guardados en: {csv_path}")
