"""
Build a realistic human hand model in Blender using mesh skinning approach.
The hand is built as a single joined mesh with proper topology.
Uses metaballs converted to mesh for organic shape, then refined.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------------------
# 0. Cleanup: remove any previous hand objects and create a new collection
# ---------------------------------------------------------------------------
hand_col_name = "Hand_Model"
# Remove existing collection if present
if hand_col_name in bpy.data.collections:
    col = bpy.data.collections[hand_col_name]
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(col)

hand_col = bpy.data.collections.new(hand_col_name)
bpy.context.scene.collection.children.link(hand_col)

# Deselect everything
bpy.ops.object.select_all(action='DESELECT')

# ---------------------------------------------------------------------------
# 1. Build the hand using a Skin modifier approach on a skeleton of vertices
#    This gives the most natural organic shape for a hand
# ---------------------------------------------------------------------------

# Create the skeleton mesh - vertices connected by edges that define the hand shape
verts = []
edges = []

# All measurements in meters (hand is roughly 0.19m / 19cm long)
# We'll build the hand palm-down, fingers pointing +Y, thumb on -X side

# ---- WRIST ----
wrist = Vector((0.0, 0.0, 0.0))
verts.append(wrist)  # 0 - wrist center

# ---- PALM ----
palm_mid = Vector((0.0, 0.06, 0.0))
verts.append(palm_mid)  # 1 - mid palm

palm_top = Vector((0.0, 0.10, 0.0))
verts.append(palm_top)  # 2 - top of palm (knuckle line base)

# Edges: wrist -> palm
edges.append((0, 1))
edges.append((1, 2))

# ---- FINGERS ----
# Finger data: (name, x_offset from center at knuckle, total_length, segment_ratios)
# segment_ratios: (metacarpal_knuckle_offset, proximal, middle, distal)
finger_data = [
    ("index",  -0.025, 0.080, (0.005, 0.038, 0.023, 0.019)),
    ("middle",  0.000, 0.088, (0.008, 0.042, 0.026, 0.020)),
    ("ring",    0.025, 0.082, (0.005, 0.039, 0.024, 0.019)),
    ("pinky",   0.048, 0.065, (0.000, 0.030, 0.019, 0.016)),
]

finger_tips = {}
finger_bases = {}
vi = len(verts)  # vertex index counter

for name, x_off, total_len, (mc_off, prox, mid, dist) in finger_data:
    base_y = palm_top.y + mc_off
    base = Vector((x_off, base_y, 0.0))
    verts.append(base)  # knuckle
    finger_bases[name] = vi
    
    p1 = base + Vector((0, prox, 0))
    verts.append(p1)  # first joint (PIP)
    
    p2 = p1 + Vector((0, mid, 0))
    verts.append(p2)  # second joint (DIP)
    
    p3 = p2 + Vector((0, dist, 0))
    verts.append(p3)  # fingertip
    finger_tips[name] = vi + 3
    
    # Connect to palm
    edges.append((2, vi))  # palm_top -> knuckle
    # Connect finger segments
    edges.append((vi, vi+1))
    edges.append((vi+1, vi+2))
    edges.append((vi+2, vi+3))
    
    vi += 4

# ---- THUMB ----
# Thumb emerges from the side of the palm, angled outward
thumb_base = Vector((-0.045, 0.03, 0.005))
verts.append(thumb_base)  # CMC joint
thumb_vi = vi

thumb_mid1 = thumb_base + Vector((-0.020, 0.025, 0.005))
verts.append(thumb_mid1)  # MCP joint

thumb_mid2 = thumb_mid1 + Vector((-0.010, 0.028, 0.003))
verts.append(thumb_mid2)  # IP joint

thumb_tip = thumb_mid2 + Vector((-0.005, 0.022, 0.001))
verts.append(thumb_tip)  # tip

# Connect thumb to palm
edges.append((1, thumb_vi))  # palm_mid -> thumb base
edges.append((thumb_vi, thumb_vi+1))
edges.append((thumb_vi+1, thumb_vi+2))
edges.append((thumb_vi+2, thumb_vi+3))

vi += 4

# ---------------------------------------------------------------------------
# 2. Create the mesh object
# ---------------------------------------------------------------------------
mesh = bpy.data.meshes.new("Hand_Skeleton")
mesh.from_pydata([v[:] for v in verts], edges, [])
mesh.update()

hand_obj = bpy.data.objects.new("Hand", mesh)
hand_col.objects.link(hand_obj)
bpy.context.view_layer.objects.active = hand_obj
hand_obj.select_set(True)

# ---------------------------------------------------------------------------
# 3. Add Skin modifier with per-vertex radii for realistic proportions
# ---------------------------------------------------------------------------
skin_mod = hand_obj.modifiers.new("Skin", 'SKIN')

# Set vertex radii for each part
# (rx, ry) - radii in local X and Z (since Y is along the finger)
radii = {}

# Wrist
radii[0] = (0.032, 0.022)  # wide, flatter wrist

# Palm
radii[1] = (0.042, 0.018)  # wide, flat palm
radii[2] = (0.045, 0.015)  # knuckle line - widest, flattest

# Fingers - each has 4 verts: knuckle, PIP, DIP, tip
finger_radii = {
    "index":  [(0.009, 0.010), (0.008, 0.009), (0.007, 0.008), (0.005, 0.006)],
    "middle": [(0.010, 0.011), (0.009, 0.010), (0.008, 0.009), (0.006, 0.007)],
    "ring":   [(0.009, 0.010), (0.008, 0.009), (0.007, 0.008), (0.005, 0.006)],
    "pinky":  [(0.007, 0.008), (0.006, 0.007), (0.005, 0.006), (0.004, 0.005)],
}

base_vi = 3  # first finger vertex
for name in ["index", "middle", "ring", "pinky"]:
    for j, (rx, ry) in enumerate(finger_radii[name]):
        radii[base_vi + j] = (rx, ry)
    base_vi += 4

# Thumb
thumb_radii = [(0.012, 0.013), (0.011, 0.012), (0.010, 0.010), (0.008, 0.009)]
for j, (rx, ry) in enumerate(thumb_radii):
    radii[thumb_vi - 4 + j] = (rx, ry)  # thumb_vi was incremented by 4

# Apply radii
for v in hand_obj.data.vertices:
    sv = hand_obj.data.skin_vertices[0].data[v.index]
    if v.index in radii:
        rx, ry = radii[v.index]
        sv.radius = (rx, ry)
    # Mark the wrist as root
    if v.index == 0:
        sv.use_root = True

# ---------------------------------------------------------------------------
# 4. Add Subdivision Surface for smoothness
# ---------------------------------------------------------------------------
subsurf = hand_obj.modifiers.new("Subdivision", 'SUBSURF')
subsurf.levels = 2
subsurf.render_levels = 3

# ---------------------------------------------------------------------------
# 5. Apply modifiers to get final mesh
# ---------------------------------------------------------------------------
bpy.context.view_layer.objects.active = hand_obj
# Apply Skin first, then Subdivision
bpy.ops.object.modifier_apply(modifier="Skin")
bpy.ops.object.modifier_apply(modifier="Subdivision")

# ---------------------------------------------------------------------------
# 6. Add Smooth shading
# ---------------------------------------------------------------------------
bpy.ops.object.shade_smooth()

# ---------------------------------------------------------------------------
# 7. Create realistic skin material with SSS
# ---------------------------------------------------------------------------
mat = bpy.data.materials.new("Skin_Material")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear default nodes
for n in nodes:
    nodes.remove(n)

# Principled BSDF
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.location = (0, 0)

# Skin color - light warm tone
bsdf.inputs['Base Color'].default_value = (0.76, 0.57, 0.46, 1.0)

# Subsurface scattering for skin translucency
bsdf.inputs['Subsurface Weight'].default_value = 0.3
bsdf.inputs['Subsurface Radius'].default_value = (0.1, 0.05, 0.02)
# SSS color slightly redder/warmer
bsdf.inputs['Subsurface Scale'].default_value = 0.01

# Skin roughness
bsdf.inputs['Roughness'].default_value = 0.45

# Slight specular
bsdf.inputs['Specular IOR Level'].default_value = 0.4

# Output
output = nodes.new('ShaderNodeOutputMaterial')
output.location = (300, 0)
links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

# Assign material
hand_obj.data.materials.append(mat)

# ---------------------------------------------------------------------------
# 8. Add fingernail geometry (simple flattened cubes on each fingertip)
# ---------------------------------------------------------------------------
def create_nail(name, tip_pos, direction, size=(0.007, 0.012, 0.002), is_thumb=False):
    """Create a simple nail mesh at a fingertip."""
    if is_thumb:
        size = (0.009, 0.013, 0.002)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=tip_pos)
    nail = bpy.context.active_object
    nail.name = f"Nail_{name}"
    nail.scale = size
    
    # Move nail to top of fingertip
    nail.location.z += size[2] + 0.003
    # Shift slightly back from tip
    nail.location.y -= size[1] * 0.3
    
    # Smooth
    bpy.ops.object.shade_smooth()
    
    # Nail material
    nail_mat = bpy.data.materials.new(f"Nail_Material_{name}")
    nail_mat.use_nodes = True
    n = nail_mat.node_tree.nodes
    n["Principled BSDF"].inputs['Base Color'].default_value = (0.88, 0.82, 0.78, 1.0)
    n["Principled BSDF"].inputs['Roughness'].default_value = 0.2
    n["Principled BSDF"].inputs['Specular IOR Level'].default_value = 0.6
    # Slight translucency
    n["Principled BSDF"].inputs['Subsurface Weight'].default_value = 0.15
    n["Principled BSDF"].inputs['Subsurface Radius'].default_value = (0.05, 0.02, 0.02)
    nail.data.materials.append(nail_mat)
    
    # Add subdivision
    sub = nail.modifiers.new("Sub", 'SUBSURF')
    sub.levels = 2
    
    # Move to hand collection
    bpy.context.scene.collection.objects.unlink(nail)
    hand_col.objects.link(nail)
    
    return nail

# Get fingertip positions from the mesh vertices
# We'll place nails at approximate tip locations based on our skeleton
tip_positions = {
    "index":  verts[finger_tips["index"]],
    "middle": verts[finger_tips["middle"]],
    "ring":   verts[finger_tips["ring"]],
    "pinky":  verts[finger_tips["pinky"]],
    "thumb":  verts[thumb_vi - 1],  # last thumb vertex
}

nail_objects = []
for fname, tpos in tip_positions.items():
    nail = create_nail(fname, tpos, Vector((0, 1, 0)), is_thumb=(fname == "thumb"))
    nail_objects.append(nail)

# ---------------------------------------------------------------------------
# 9. Join all nails with the hand
# ---------------------------------------------------------------------------
bpy.ops.object.select_all(action='DESELECT')
hand_obj.select_set(True)
for nail in nail_objects:
    nail.select_set(True)
bpy.context.view_layer.objects.active = hand_obj
bpy.ops.object.join()

# ---------------------------------------------------------------------------
# 10. Add subtle knuckle detail with a Displace modifier + texture
# ---------------------------------------------------------------------------
# Create a clouds texture for skin detail
tex = bpy.data.textures.new("Skin_Bump", type='CLOUDS')
tex.noise_scale = 0.3
tex.noise_depth = 3

displace = hand_obj.modifiers.new("Skin_Detail", 'DISPLACE')
displace.texture = tex
displace.strength = 0.001  # Very subtle
displace.mid_level = 0.5

# ---------------------------------------------------------------------------
# 11. Position the hand nicely in the scene (away from the Tesla)
# ---------------------------------------------------------------------------
hand_obj.location = (3.0, 0.0, 1.0)  # Place to the right of existing objects
hand_obj.rotation_euler = (0, 0, 0)

# Scale up for visibility (the hand is modeled at real-world scale ~19cm)
# Keep it at 1:1 scale but make sure it's visible
hand_obj.scale = (5, 5, 5)  # Scale up 5x for visibility in the scene

# ---------------------------------------------------------------------------
# 12. Set up a camera and light for the hand
# ---------------------------------------------------------------------------
# Camera
cam_data = bpy.data.cameras.new("Hand_Camera")
cam_data.lens = 85  # Portrait lens for hand detail
cam_obj = bpy.data.objects.new("Camera - hand", cam_data)
cam_obj.location = (3.0, -1.5, 1.8)
cam_obj.rotation_euler = (math.radians(55), 0, 0)
hand_col.objects.link(cam_obj)

# Key light
key_light_data = bpy.data.lights.new("Hand_Key_Light", type='AREA')
key_light_data.energy = 100
key_light_data.size = 1.0
key_light = bpy.data.objects.new("Hand_Key_Light", key_light_data)
key_light.location = (2.0, -0.5, 2.5)
key_light.rotation_euler = (math.radians(45), math.radians(-20), 0)
hand_col.objects.link(key_light)

# Fill light
fill_light_data = bpy.data.lights.new("Hand_Fill_Light", type='AREA')
fill_light_data.energy = 40
fill_light_data.size = 1.5
fill_light = bpy.data.objects.new("Hand_Fill_Light", fill_light_data)
fill_light.location = (4.5, 0.5, 1.5)
fill_light.rotation_euler = (math.radians(30), math.radians(30), 0)
hand_col.objects.link(fill_light)

# ---------------------------------------------------------------------------
# 13. Load reference images and pack them
# ---------------------------------------------------------------------------
ref_dir = "/Users/thomasthemaker/Development/ComfySpace/playground/Blender&AI/"
ref_files = [
    "hand_palm_view.jpg",
    "hand_back_view.jpg",
    "hand_side_view.jpg",
    "hand_fist_view.jpg",
]

for rf in ref_files:
    path = ref_dir + rf
    try:
        img = bpy.data.images.load(path)
        img.pack()
    except Exception as e:
        print(f"Warning: Could not load reference {rf}: {e}")

print("Hand model created successfully!")
print(f"Object: {hand_obj.name}")
print(f"Vertices: {len(hand_obj.data.vertices)}")
print(f"Faces: {len(hand_obj.data.polygons)}")
print(f"Collection: {hand_col_name}")
