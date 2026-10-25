"""Render all studio views of the Tesla Model 3 (Highland) in Blender."""

import bpy
from pathlib import Path

ROOT = Path("/Users/thomasthemaker/Development/ComfySpace/playground/Blender&AI")
scene = bpy.context.scene

views = [
    ("Camera - hero",  "tesla-hero.png"),
    ("Camera - front", "tesla-front.png"),
    ("Camera - side",  "tesla-side.png"),
    ("Camera - rear",  "tesla-rear.png"),
    ("Camera - top",   "tesla-top.png"),
]

for cam_name, filename in views:
    cam = bpy.data.objects.get(cam_name)
    if cam:
        scene.camera = cam
        out_path = str(ROOT / filename)
        scene.render.filepath = out_path
        print(f"Rendering {cam_name} to {out_path}...")
        bpy.ops.render.render(write_still=True)
        print(f"Done {filename}")
    else:
        print(f"Warning: camera {cam_name} not found")

print("All views rendered successfully.")
