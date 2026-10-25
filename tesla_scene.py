"""Refined procedural Tesla Model 3 (Highland) 3D Scene for Blender.
Directly referenced from multi-view studio reference images:
  - Front view (symmetrical fascia, horizontal slit LED headlights, lower intake)
  - Front 3/4 hero view (hood sculpting, aero wheels, cabin greenhouse)
  - Side view (aerodynamic fastback profile, flush handles, rocker trim)
  - Rear view (Highland C-clamp wrap-around taillights, ducktail spoiler, rear diffuser)
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# 1. Clean scene initialization
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for col in list(bpy.data.collections):
    bpy.data.collections.remove(col)

scene = bpy.context.scene
scene.name = "Tesla_Model_3"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.color = (0.78, 0.79, 0.82)


def link_obj(obj, col=None):
    if obj.name not in scene.collection.objects:
        scene.collection.objects.link(obj)
    return obj


# 2. Material Helper
def create_mat(name, base_color, metallic=0.0, roughness=0.5, coat_weight=0.0, 
               coat_roughness=0.03, transmission_weight=0.0, ior=1.5, 
               emission_color=(0, 0, 0), emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        return mat
    
    inputs = bsdf.inputs
    if "Base Color" in inputs:
        inputs["Base Color"].default_value = (*base_color, 1.0) if len(base_color) == 3 else base_color
    if "Metallic" in inputs:
        inputs["Metallic"].default_value = metallic
    if "Roughness" in inputs:
        inputs["Roughness"].default_value = roughness
    if "Coat Weight" in inputs:
        inputs["Coat Weight"].default_value = coat_weight
    if "Coat Roughness" in inputs:
        inputs["Coat Roughness"].default_value = coat_roughness
    if "Transmission Weight" in inputs:
        inputs["Transmission Weight"].default_value = transmission_weight
    if "IOR" in inputs:
        inputs["IOR"].default_value = ior
    if "Emission Color" in inputs:
        inputs["Emission Color"].default_value = (*emission_color, 1.0) if len(emission_color) == 3 else emission_color
    if "Emission Strength" in inputs:
        inputs["Emission Strength"].default_value = emission_strength
    return mat

# Materials
mat_carpaint = create_mat("Tesla_Pearl_White", (0.92, 0.93, 0.95), metallic=0.06, roughness=0.12, coat_weight=1.0, coat_roughness=0.02)
mat_satin_black = create_mat("Tesla_Satin_Black", (0.020, 0.020, 0.022), metallic=0.1, roughness=0.45)
mat_gloss_black = create_mat("Tesla_Gloss_Black", (0.010, 0.010, 0.012), metallic=0.2, roughness=0.05, coat_weight=1.0)
mat_tinted_glass = create_mat("Tesla_Panoramic_Glass", (0.015, 0.018, 0.022), metallic=0.15, roughness=0.02, coat_weight=1.0, coat_roughness=0.01)
mat_headlight_glass = create_mat("Tesla_Headlight_Glass", (0.95, 0.96, 0.98), metallic=0.0, roughness=0.02, transmission_weight=0.90, ior=1.49)
mat_headlight_led = create_mat("Tesla_Headlight_LED", (1.0, 1.0, 1.0), roughness=0.05, emission_color=(1.0, 1.0, 1.0), emission_strength=25.0)
mat_taillight_led = create_mat("Tesla_Taillight_LED", (1.0, 0.02, 0.01), roughness=0.08, emission_color=(1.0, 0.02, 0.01), emission_strength=22.0)
mat_taillight_glass = create_mat("Tesla_Taillight_Lens", (0.75, 0.02, 0.01), roughness=0.05, transmission_weight=0.75, ior=1.49)
mat_chrome = create_mat("Tesla_Chrome", (0.96, 0.96, 0.97), metallic=1.0, roughness=0.04)
mat_tire_rubber = create_mat("Tesla_Tire_Rubber", (0.025, 0.025, 0.028), metallic=0.0, roughness=0.82)
mat_aero_wheel = create_mat("Tesla_Aero_Wheel", (0.030, 0.032, 0.038), metallic=0.85, roughness=0.22)
mat_brake_rotor = create_mat("Tesla_Brake_Rotor", (0.75, 0.75, 0.78), metallic=0.95, roughness=0.25)
mat_brake_caliper = create_mat("Tesla_Brake_Caliper", (0.08, 0.08, 0.09), metallic=0.5, roughness=0.35)
mat_interior_charcoal = create_mat("Tesla_Interior_Charcoal", (0.025, 0.025, 0.028), roughness=0.85)
mat_screen_ui = create_mat("Tesla_Screen_UI", (0.1, 0.15, 0.22), roughness=0.1, emission_color=(0.35, 0.50, 0.70), emission_strength=3.0)
mat_studio_floor = create_mat("Studio_Floor_Mat", (0.87, 0.88, 0.90), metallic=0.0, roughness=0.16)


# 3. Precision Tesla Body Mesh
def create_tesla_body():
    bm = bmesh.new()
    
    # 14 cross-sectional profile stations along Y (rear to front)
    # Each slice contains 10 points:
    # 0: Left rocker / underbody
    # 1: Left lower crease / wheel arch lower
    # 2: Left beltline / shoulder crease
    # 3: Left window sill / hood side crest
    # 4: Left hood / roof edge
    # 5: Right hood / roof edge
    # 6: Right window sill / hood side crest
    # 7: Right beltline / shoulder crease
    # 8: Right lower crease / wheel arch lower
    # 9: Right rocker / underbody
    
    stations = [
        # Y = -2.36 (Rear bumper bottom)
        (-2.36, [(-0.55, 0.18), (-0.82, 0.35), (-0.84, 0.65), (-0.78, 0.84), (-0.45, 0.88),
                 (0.45, 0.88),  (0.78, 0.84),  (0.84, 0.65),  (0.82, 0.35),  (0.55, 0.18)]),
        # Y = -2.25 (Rear fascia / taillight shelf)
        (-2.25, [(-0.62, 0.18), (-0.86, 0.45), (-0.89, 0.72), (-0.82, 0.94), (-0.48, 0.96),
                 (0.48, 0.96),  (0.82, 0.94),  (0.89, 0.72),  (0.86, 0.45),  (0.62, 0.18)]),
        # Y = -2.10 (Trunk ducktail spoiler edge)
        (-2.10, [(-0.68, 0.16), (-0.89, 0.50), (-0.92, 0.80), (-0.84, 1.02), (-0.48, 1.05),
                 (0.48, 1.05),  (0.84, 1.02),  (0.92, 0.80),  (0.89, 0.50),  (0.68, 0.16)]),
        # Y = -1.82 (Rear glass bottom / trunk seam)
        (-1.82, [(-0.72, 0.15), (-0.91, 0.55), (-0.93, 0.84), (-0.78, 1.08), (-0.46, 1.12),
                 (0.46, 1.12),  (0.78, 1.08),  (0.93, 0.84),  (0.91, 0.55),  (0.72, 0.15)]),
        # Y = -1.44 (Rear wheel arch)
        (-1.44, [(-0.72, 0.20), (-0.90, 0.64), (-0.93, 0.86), (-0.74, 1.22), (-0.45, 1.27),
                 (0.45, 1.27),  (0.74, 1.22),  (0.93, 0.86),  (0.90, 0.64),  (0.72, 0.20)]),
        # Y = -1.05 (C-pillar)
        (-1.05, [(-0.73, 0.14), (-0.88, 0.56), (-0.92, 0.86), (-0.70, 1.34), (-0.44, 1.38),
                 (0.44, 1.38),  (0.70, 1.34),  (0.92, 0.86),  (0.88, 0.56),  (0.73, 0.14)]),
        # Y = -0.40 (B-pillar rear door)
        (-0.40, [(-0.73, 0.14), (-0.87, 0.54), (-0.91, 0.86), (-0.66, 1.40), (-0.43, 1.43),
                 (0.43, 1.43),  (0.66, 1.40),  (0.91, 0.86),  (0.87, 0.54),  (0.73, 0.14)]),
        # Y = +0.10 (Roof apex)
        (0.10,  [(-0.73, 0.14), (-0.87, 0.54), (-0.91, 0.86), (-0.65, 1.41), (-0.42, 1.44),
                 (0.42, 1.44),  (0.65, 1.41),  (0.91, 0.86),  (0.87, 0.54),  (0.73, 0.14)]),
        # Y = +0.70 (A-pillar / front door)
        (0.70,  [(-0.72, 0.14), (-0.86, 0.54), (-0.90, 0.85), (-0.66, 1.28), (-0.42, 1.32),
                 (0.42, 1.32),  (0.66, 1.28),  (0.90, 0.85),  (0.86, 0.54),  (0.72, 0.14)]),
        # Y = +1.15 (Windshield cowl / hood base)
        (1.15,  [(-0.70, 0.14), (-0.86, 0.54), (-0.89, 0.83), (-0.66, 0.92), (-0.38, 0.89),
                 (0.38, 0.89),  (0.66, 0.92),  (0.89, 0.83),  (0.86, 0.54),  (0.70, 0.14)]),
        # Y = +1.44 (Front wheel arch)
        (1.44,  [(-0.70, 0.20), (-0.88, 0.62), (-0.91, 0.81), (-0.66, 0.86), (-0.36, 0.82),
                 (0.36, 0.82),  (0.66, 0.86),  (0.91, 0.81),  (0.88, 0.62),  (0.70, 0.20)]),
        # Y = +1.95 (Front fender front taper / headlights)
        (1.95,  [(-0.64, 0.16), (-0.82, 0.48), (-0.86, 0.74), (-0.62, 0.76), (-0.32, 0.72),
                 (0.32, 0.72),  (0.62, 0.76),  (0.86, 0.74),  (0.82, 0.48),  (0.64, 0.16)]),
        # Y = +2.20 (Shark nose leading crease)
        (2.20,  [(-0.55, 0.18), (-0.76, 0.42), (-0.79, 0.64), (-0.54, 0.66), (-0.26, 0.62),
                 (0.26, 0.62),  (0.54, 0.66),  (0.79, 0.64),  (0.76, 0.42),  (0.55, 0.18)]),
        # Y = +2.34 (Front lower bumper chin & intake)
        (2.34,  [(-0.46, 0.15), (-0.68, 0.32), (-0.68, 0.52), (-0.46, 0.54), (-0.22, 0.52),
                 (0.22, 0.52),  (0.46, 0.54),  (0.68, 0.52),  (0.68, 0.32),  (0.46, 0.15)])
    ]
    
    slice_verts = []
    for y, pts in stations:
        v_list = [bm.verts.new((x, y, z)) for x, z in pts]
        slice_verts.append(v_list)
        
    bm.verts.ensure_lookup_table()
    
    # Connect body rings with quad faces
    for i in range(len(stations) - 1):
        s1 = slice_verts[i]
        s2 = slice_verts[i + 1]
        for j in range(len(s1) - 1):
            bm.faces.new((s1[j], s2[j], s2[j + 1], s1[j + 1]))
        # Connect bottom underbody
        bm.faces.new((s1[0], s1[9], s2[9], s2[0]))
        
    # Cap rear fascia
    r = slice_verts[0]
    bm.faces.new((r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]))
    # Cap front nose
    f = slice_verts[-1]
    bm.faces.new((f[9], f[8], f[7], f[6], f[5], f[4], f[3], f[2], f[1], f[0]))
    
    mesh = bpy.data.meshes.new("Tesla_Model_3_Body")
    bm.to_mesh(mesh)
    bm.free()
    
    body = bpy.data.objects.new("Tesla_Model_3_Body", mesh)
    link_obj(body)
    body.data.materials.append(mat_carpaint)
    for p in mesh.polygons:
        p.use_smooth = True
        
    subsurf = body.modifiers.new("Subsurf", "SUBSURF")
    subsurf.levels = 2
    subsurf.render_levels = 2
    return body


# 4. Continuous Panoramic Glass Canopy (Windshield, Roof & Rear Glass)
def create_glass_canopy():
    bm = bmesh.new()
    
    canopy_stations = [
        # Y, [(X, Z)] from left to right
        (1.16, [(-0.64, 0.91), (-0.35, 0.895), (0.0, 0.89),  (0.35, 0.895), (0.64, 0.91)]),  # Windshield bottom
        (0.70, [(-0.62, 1.30), (-0.33, 1.325), (0.0, 1.335), (0.33, 1.325), (0.62, 1.30)]),  # Windshield mid
        (0.10, [(-0.61, 1.42), (-0.32, 1.442), (0.0, 1.45),  (0.32, 1.442), (0.61, 1.42)]),  # Roof peak
        (-0.40,[(-0.62, 1.41), (-0.33, 1.432), (0.0, 1.44),  (0.33, 1.432), (0.62, 1.41)]),  # Center roof
        (-1.05,[(-0.64, 1.36), (-0.35, 1.385), (0.0, 1.392), (0.35, 1.385), (0.64, 1.36)]),  # Rear passenger
        (-1.45,[(-0.68, 1.24), (-0.37, 1.272), (0.0, 1.28),  (0.37, 1.272), (0.68, 1.24)]),  # Rear window mid
        (-1.82,[(-0.73, 1.10), (-0.39, 1.125), (0.0, 1.13),  (0.39, 1.125), (0.73, 1.10)])   # Rear glass bottom
    ]
    
    slice_verts = []
    for y, pts in canopy_stations:
        v_list = [bm.verts.new((x, y, z + 0.005)) for x, z in pts]
        slice_verts.append(v_list)
        
    for i in range(len(canopy_stations) - 1):
        s1 = slice_verts[i]
        s2 = slice_verts[i + 1]
        for j in range(len(s1) - 1):
            bm.faces.new((s1[j], s2[j], s2[j + 1], s1[j + 1]))
            
    mesh = bpy.data.meshes.new("Tesla_Glass_Canopy")
    bm.to_mesh(mesh)
    bm.free()
    
    canopy = bpy.data.objects.new("Tesla_Glass_Canopy", mesh)
    link_obj(canopy)
    canopy.data.materials.append(mat_tinted_glass)
    for p in mesh.polygons:
        p.use_smooth = True
        
    subsurf = canopy.modifiers.new("Subsurf", "SUBSURF")
    subsurf.levels = 2
    subsurf.render_levels = 2
    return canopy


# 5. Flush Side Windows & Satin Black Pillars
def create_side_windows():
    for side in [-1, 1]:
        bm = bmesh.new()
        # Quad strip following the door greenhouse arch
        # Upper arch points (roofline) and lower arch points (beltline)
        win_stations = [
            # (Y, upper (X, Z), lower (X, Z))
            (0.85,  (side * 0.64, 1.18), (side * 0.86, 0.86)),   # Front A-pillar corner
            (0.40,  (side * 0.61, 1.38), (side * 0.88, 0.87)),   # Front door window
            (-0.15, (side * 0.61, 1.42), (side * 0.88, 0.87)),   # B-pillar divider
            (-0.70, (side * 0.62, 1.38), (side * 0.88, 0.87)),   # Rear door window
            (-1.25, (side * 0.65, 1.28), (side * 0.87, 0.87)),   # C-pillar quarterlight
            (-1.60, (side * 0.72, 1.12), (side * 0.84, 0.89))    # C-pillar rear tip
        ]
        
        top_verts = []
        bot_verts = []
        for y, top, bot in win_stations:
            v_top = bm.verts.new((top[0], y, top[1]))
            v_bot = bm.verts.new((bot[0], y, bot[1]))
            top_verts.append(v_top)
            bot_verts.append(v_bot)
            
        for i in range(len(win_stations) - 1):
            bm.faces.new((bot_verts[i], bot_verts[i + 1], top_verts[i + 1], top_verts[i]))
            
        mesh = bpy.data.meshes.new(f"Tesla_Side_Window_{'R' if side > 0 else 'L'}")
        bm.to_mesh(mesh)
        bm.free()
        
        win = bpy.data.objects.new(mesh.name, mesh)
        link_obj(win)
        win.data.materials.append(mat_tinted_glass)
        for p in mesh.polygons:
            p.use_smooth = True
            
        # Flush Black B-pillar trim strip
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.75, -0.15, 1.14),
            scale=(0.015, 0.08, 0.48)
        )
        bp = bpy.context.object
        bp.name = f"Tesla_B_Pillar_{'R' if side > 0 else 'L'}"
        bp.rotation_euler = (0, math.radians(side * 14), 0)
        link_obj(bp)
        bp.data.materials.append(mat_gloss_black)


# 6. Sleek Highland LED Headlights
def create_headlights():
    for side in [-1, 1]:
        # Highland horizontal slit headlight housing
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.60, 2.12, 0.61),
            scale=(0.42, 0.10, 0.045)
        )
        hl = bpy.context.object
        hl.name = f"Tesla_Headlight_Housing_{'R' if side > 0 else 'L'}"
        hl.rotation_euler = (math.radians(-6), math.radians(side * 6), math.radians(-side * 20))
        link_obj(hl)
        hl.data.materials.append(mat_gloss_black)

        # Sharp horizontal LED DRL light guide
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.012, depth=0.38,
            location=(side * 0.60, 2.15, 0.615),
            rotation=(math.radians(-6), math.radians(90), math.radians(-side * 20 + 90))
        )
        drl = bpy.context.object
        drl.name = f"Tesla_DRL_LED_{'R' if side > 0 else 'L'}"
        link_obj(drl)
        drl.data.materials.append(mat_headlight_led)

        # Polycarbonate clear outer lens
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.60, 2.16, 0.61),
            scale=(0.44, 0.02, 0.05)
        )
        lens = bpy.context.object
        lens.name = f"Tesla_Headlight_Lens_{'R' if side > 0 else 'L'}"
        lens.rotation_euler = hl.rotation_euler
        link_obj(lens)
        lens.data.materials.append(mat_headlight_glass)


# 7. Rear C-Clamp Wrap-Around Taillights
def create_taillights():
    for side in [-1, 1]:
        # Main horizontal taillight blade
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.64, -2.25, 0.94),
            scale=(0.42, 0.06, 0.045)
        )
        tl = bpy.context.object
        tl.name = f"Tesla_Taillight_{'R' if side > 0 else 'L'}"
        tl.rotation_euler = (math.radians(-8), math.radians(side * 4), math.radians(side * 14))
        link_obj(tl)
        tl.data.materials.append(mat_taillight_led)

        # Outer corner hook (C-clamp return wrapping around the rear quarter panel)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.84, -2.18, 0.94),
            scale=(0.04, 0.16, 0.045)
        )
        tl_hook = bpy.context.object
        tl_hook.name = f"Tesla_Taillight_Hook_{'R' if side > 0 else 'L'}"
        tl_hook.rotation_euler = (0, 0, math.radians(side * 8))
        link_obj(tl_hook)
        tl_hook.data.materials.append(mat_taillight_led)

        # Red tinted outer lens cover
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.64, -2.27, 0.94),
            scale=(0.44, 0.03, 0.055)
        )
        tll = bpy.context.object
        tll.name = f"Tesla_Taillight_Lens_{'R' if side > 0 else 'L'}"
        tll.rotation_euler = tl.rotation_euler
        link_obj(tll)
        tll.data.materials.append(mat_taillight_glass)


# 8. Lower Fascia Trims (Front Intake, Splitter, Rear Diffuser)
def create_trims():
    # Front lower intake recess (matte black)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 2.29, 0.23),
        scale=(1.05, 0.10, 0.065)
    )
    intake = bpy.context.object
    intake.name = "Tesla_Front_Intake"
    link_obj(intake)
    intake.data.materials.append(mat_satin_black)

    # Front chin splitter
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 2.32, 0.16),
        scale=(1.22, 0.08, 0.022)
    )
    splitter = bpy.context.object
    splitter.name = "Tesla_Front_Splitter"
    link_obj(splitter)
    splitter.data.materials.append(mat_satin_black)

    # Side rocker skirts (left & right)
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.88, 0.0, 0.16),
            scale=(0.04, 2.6, 0.04)
        )
        skirt = bpy.context.object
        skirt.name = f"Tesla_Rocker_Skirt_{'R' if side > 0 else 'L'}"
        link_obj(skirt)
        skirt.data.materials.append(mat_satin_black)

    # Rear diffuser / lower apron
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, -2.28, 0.27),
        scale=(1.38, 0.15, 0.16)
    )
    diffuser = bpy.context.object
    diffuser.name = "Tesla_Rear_Diffuser"
    diffuser.rotation_euler = (math.radians(-16), 0, 0)
    link_obj(diffuser)
    diffuser.data.materials.append(mat_satin_black)

    # Rear slim red reflectors
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.60, -2.31, 0.28),
            scale=(0.16, 0.02, 0.022)
        )
        ref = bpy.context.object
        ref.name = f"Tesla_Rear_Reflector_{'R' if side > 0 else 'L'}"
        ref.rotation_euler = (math.radians(-16), 0, math.radians(side * 8))
        link_obj(ref)
        ref.data.materials.append(mat_taillight_glass)


# 9. Exterior Details (Mirrors, Flush Handles, Badges, Autopilot Cameras)
def create_exterior_details():
    # Side Mirrors
    for side in [-1, 1]:
        # Mirror housing
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.98, 0.85, 0.96),
            scale=(0.12, 0.20, 0.09)
        )
        m = bpy.context.object
        m.name = f"Tesla_Mirror_Housing_{'R' if side > 0 else 'L'}"
        m.rotation_euler = (math.radians(6), math.radians(side * 12), math.radians(-side * 10))
        link_obj(m)
        m.data.materials.append(mat_carpaint)

        # Mirror arm
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.018, depth=0.14,
            location=(side * 0.91, 0.86, 0.93),
            rotation=(math.radians(20), math.radians(-side * 60), 0)
        )
        arm = bpy.context.object
        arm.name = f"Tesla_Mirror_Arm_{'R' if side > 0 else 'L'}"
        link_obj(arm)
        arm.data.materials.append(mat_satin_black)

        # Mirror glass insert
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.98, 0.84, 0.96),
            scale=(0.015, 0.18, 0.08)
        )
        mg = bpy.context.object
        mg.name = f"Tesla_Mirror_Glass_{'R' if side > 0 else 'L'}"
        mg.rotation_euler = m.rotation_euler
        link_obj(mg)
        mg.data.materials.append(mat_chrome)

    # Flush Door Handles (4 doors)
    handles = [
        ("Front_L", -0.90, 0.55, 0.84),
        ("Front_R",  0.90, 0.55, 0.84),
        ("Rear_L",  -0.90, -0.45, 0.85),
        ("Rear_R",   0.90, -0.45, 0.85)
    ]
    for name, x, y, z in handles:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, y, z),
            scale=(0.012, 0.13, 0.028)
        )
        h = bpy.context.object
        h.name = f"Tesla_Door_Handle_{name}"
        link_obj(h)
        h.data.materials.append(mat_satin_black)

    # Front Fender Autopilot Cameras
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.90, 1.05, 0.76),
            scale=(0.015, 0.07, 0.026)
        )
        cam = bpy.context.object
        cam.name = f"Tesla_Autopilot_Camera_{'R' if side > 0 else 'L'}"
        link_obj(cam)
        cam.data.materials.append(mat_gloss_black)

    # Hood Tesla "T" Badge
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.03, depth=0.006,
        location=(0.0, 2.14, 0.68),
        rotation=(math.radians(65), 0, 0)
    )
    badge = bpy.context.object
    badge.name = "Tesla_Hood_Badge"
    link_obj(badge)
    badge.data.materials.append(mat_chrome)


# 10. Accurate 18" Aero Wheels & Tires (Direct World Coordinates)
def create_wheels():
    wheel_positions = [
        ("Front_Left",  -0.81,  1.438, 0.334, -1),
        ("Front_Right",  0.81,  1.438, 0.334,  1),
        ("Rear_Left",   -0.81, -1.437, 0.334, -1),
        ("Rear_Right",   0.81, -1.437, 0.334,  1)
    ]
    
    for name, wx, wy, wz, side in wheel_positions:
        # Rubber Tire (Radius 0.334m, Width 0.235m)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.334, depth=0.235, vertices=48,
            location=(wx, wy, wz),
            rotation=(0, math.radians(90), 0)
        )
        tire = bpy.context.object
        tire.name = f"Tire_{name}"
        link_obj(tire)
        tire.data.materials.append(mat_tire_rubber)
        for p in tire.data.polygons:
            p.use_smooth = True
        bev = tire.modifiers.new("Bevel", "BEVEL")
        bev.width = 0.035
        bev.segments = 4

        # 18" Aero Wheel Cover (Radius 0.245m, sits on outer wheel face)
        outer_x = wx + side * 0.112
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.245, depth=0.022, vertices=36,
            location=(outer_x, wy, wz),
            rotation=(0, math.radians(90), 0)
        )
        rim = bpy.context.object
        rim.name = f"Aero_Wheel_Cover_{name}"
        link_obj(rim)
        rim.data.materials.append(mat_aero_wheel)
        for p in rim.data.polygons:
            p.use_smooth = True

        # 5 Directional Aero Blades
        for spoke_idx in range(5):
            angle = math.radians(spoke_idx * 72)
            by = math.cos(angle) * 0.135
            bz = math.sin(angle) * 0.135
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(outer_x + side * 0.005, wy + by, wz + bz),
                scale=(0.014, 0.065, 0.135)
            )
            spoke = bpy.context.object
            spoke.name = f"Aero_Spoke_{name}_{spoke_idx}"
            spoke.rotation_euler = (math.radians(90) - angle, 0, 0)
            link_obj(spoke)
            spoke.data.materials.append(mat_aero_wheel)

        # Center Cap with Tesla Emblem
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.042, depth=0.014, vertices=24,
            location=(outer_x + side * 0.012, wy, wz),
            rotation=(0, math.radians(90), 0)
        )
        cap = bpy.context.object
        cap.name = f"Wheel_Center_Cap_{name}"
        link_obj(cap)
        cap.data.materials.append(mat_satin_black)

        # Brake Rotor (ventilated steel disc)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.18, depth=0.02, vertices=32,
            location=(wx - side * 0.02, wy, wz),
            rotation=(0, math.radians(90), 0)
        )
        rotor = bpy.context.object
        rotor.name = f"Brake_Rotor_{name}"
        link_obj(rotor)
        rotor.data.materials.append(mat_brake_rotor)

        # Brake Caliper
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(wx - side * 0.01, wy + 0.12, wz + 0.12),
            scale=(0.05, 0.08, 0.11)
        )
        caliper = bpy.context.object
        caliper.name = f"Brake_Caliper_{name}"
        caliper.rotation_euler = (0, 0, math.radians(-35))
        link_obj(caliper)
        caliper.data.materials.append(mat_brake_caliper)


# 11. Minimalist Interior Silhouette
def create_interior():
    # Horizontal minimalist dashboard
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 0.82, 0.87),
        scale=(1.30, 0.26, 0.07)
    )
    dash = bpy.context.object
    dash.name = "Tesla_Dashboard"
    link_obj(dash)
    dash.data.materials.append(mat_interior_charcoal)

    # 15.4" Floating Central Touchscreen
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0.0, 0.68, 0.94),
        scale=(0.34, 0.016, 0.21)
    )
    screen = bpy.context.object
    screen.name = "Tesla_Touchscreen"
    screen.rotation_euler = (math.radians(-12), 0, 0)
    link_obj(screen)
    screen.data.materials.append(mat_screen_ui)

    # Steering Wheel
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.17, minor_radius=0.018,
        location=(-0.38, 0.58, 0.92),
        rotation=(math.radians(28), 0, 0)
    )
    wheel = bpy.context.object
    wheel.name = "Tesla_Steering_Wheel"
    link_obj(wheel)
    wheel.data.materials.append(mat_satin_black)

    # Front Seats
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.38, 0.10, 0.52),
            scale=(0.44, 0.50, 0.15)
        )
        cushion = bpy.context.object
        cushion.name = f"Tesla_Front_Seat_Cushion_{'R' if side > 0 else 'L'}"
        link_obj(cushion)
        cushion.data.materials.append(mat_interior_charcoal)
        
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * 0.38, -0.16, 0.88),
            scale=(0.42, 0.15, 0.56)
        )
        back = bpy.context.object
        back.name = f"Tesla_Front_Seat_Back_{'R' if side > 0 else 'L'}"
        back.rotation_euler = (math.radians(-14), 0, 0)
        link_obj(back)
        back.data.materials.append(mat_interior_charcoal)


# 12. Studio Stage & Lighting (Seamless 360 Studio Cyclorama)
def create_studio_and_lighting():
    # Large seamless cyclorama studio bowl (radius 28m, height 10m)
    bm = bmesh.new()
    # Concentric rings curving upwards into an infinite studio wall
    rings = [
        (0.0, 0.0),    # Center ground
        (12.0, 0.0),   # Inner stage
        (20.0, 0.35),  # Gentle curve start
        (24.0, 2.2),   # Bevel transition
        (27.0, 6.0),   # Wall rise
        (28.0, 12.0)   # Top rim
    ]
    ring_verts = []
    num_seg = 48
    for r, z in rings:
        r_list = []
        for s in range(num_seg):
            ang = 2 * math.pi * s / num_seg
            vx = math.cos(ang) * r
            vy = math.sin(ang) * r
            r_list.append(bm.verts.new((vx, vy, z - 0.02)))
        ring_verts.append(r_list)
        
    for i in range(len(rings) - 1):
        r1 = ring_verts[i]
        r2 = ring_verts[i + 1]
        for s in range(num_seg):
            s_next = (s + 1) % num_seg
            bm.faces.new((r1[s], r1[s_next], r2[s_next], r2[s]))
            
    mesh = bpy.data.meshes.new("Studio_360_Cyclorama")
    bm.to_mesh(mesh)
    bm.free()
    
    floor = bpy.data.objects.new("Studio_360_Cyclorama", mesh)
    link_obj(floor)
    floor.data.materials.append(mat_studio_floor)
    for p in mesh.polygons:
        p.use_smooth = True

    # 1. Main Overhead Softbox (Crucial for sleek continuous roof/shoulder reflections)
    light_overhead = bpy.data.lights.new("Light_Overhead_Softbox", "AREA")
    light_overhead.energy = 5400.0
    light_overhead.size = 3.4
    light_overhead.size_y = 9.4
    light_overhead.color = (0.97, 0.98, 1.0)
    lo_obj = bpy.data.objects.new("Light_Overhead_Softbox", light_overhead)
    lo_obj.location = (0.0, 0.0, 4.8)
    link_obj(lo_obj)
    
    # 2. Key Softbox Light (Front-Left 3/4)
    light_key = bpy.data.lights.new("Light_Key_Softbox", "AREA")
    light_key.energy = 3600.0
    light_key.size = 2.8
    light_key.size_y = 3.8
    light_key.color = (1.0, 0.99, 0.97)
    lk_obj = bpy.data.objects.new("Light_Key_Softbox", light_key)
    lk_obj.location = (-4.8, 4.5, 2.6)
    lk_obj.rotation_euler = (math.radians(35), math.radians(-25), math.radians(45))
    link_obj(lk_obj)

    # 3. Fill Softbox Light (Right side)
    light_fill = bpy.data.lights.new("Light_Fill_Softbox", "AREA")
    light_fill.energy = 2200.0
    light_fill.size = 3.4
    light_fill.size_y = 3.4
    light_fill.color = (0.95, 0.97, 1.0)
    lf_obj = bpy.data.objects.new("Light_Fill_Softbox", light_fill)
    lf_obj.location = (5.2, 2.0, 2.2)
    lf_obj.rotation_euler = (math.radians(25), math.radians(35), math.radians(-70))
    link_obj(lf_obj)

    # 4. Rim / Edge Kicker Light (Rear-Right)
    light_rim = bpy.data.lights.new("Light_Rim_Kicker", "AREA")
    light_rim.energy = 3000.0
    light_rim.size = 2.4
    light_rim.size_y = 4.4
    light_rim.color = (0.96, 0.98, 1.0)
    lr_obj = bpy.data.objects.new("Light_Rim_Kicker", light_rim)
    lr_obj.location = (4.5, -4.8, 2.6)
    lr_obj.rotation_euler = (math.radians(-30), math.radians(30), math.radians(-135))
    link_obj(lr_obj)


# 13. Studio Cameras with Track-To Constraints
def create_studio_cameras():
    target_car = bpy.data.objects.new("Target_Car_Center", None)
    target_car.location = (0.0, 0.0, 0.65)
    link_obj(target_car)

    cameras = [
        ("Camera - hero",  (-4.8, 5.2, 1.65), 45.0),
        ("Camera - front", (0.0, 5.8, 0.95),  55.0),
        ("Camera - side",  (-6.4, 0.0, 1.05), 60.0),
        ("Camera - rear",  (4.8, -5.2, 1.65), 45.0),
        ("Camera - top",   (0.0, 0.01, 9.6),  28.0)
    ]
    
    first_cam = None
    for name, loc, focal in cameras:
        cam_data = bpy.data.cameras.new(name)
        cam_data.lens = focal
        cam_data.sensor_width = 36.0
        cam_obj = bpy.data.objects.new(name, cam_data)
        cam_obj.location = loc
        link_obj(cam_obj)
        
        tt = cam_obj.constraints.new(type="TRACK_TO")
        tt.target = target_car
        tt.track_axis = "TRACK_NEGATIVE_Z"
        tt.up_axis = "UP_Y"
        
        if first_cam is None:
            first_cam = cam_obj
            
    scene.camera = first_cam


# 14. Pack Reference Image Card in Viewport
def create_reference_card():
    ref_path = "/Users/thomasthemaker/Development/ComfySpace/playground/Blender&AI/tesla-reference-views.jpg"
    try:
        img = bpy.data.images.load(ref_path)
        img.pack()
        
        mat_ref = bpy.data.materials.new("Reference_Card_Material")
        mat_ref.use_nodes = True
        bsdf = mat_ref.node_tree.nodes.get("Principled BSDF")
        tex_node = mat_ref.node_tree.nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        mat_ref.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
        
        bpy.ops.mesh.primitive_plane_add(
            size=1.0,
            location=(0.0, 0.0, -0.05),
            scale=(8.0, 4.5, 1.0)
        )
        card = bpy.context.object
        card.name = "Reference_Views_Card"
        card.data.materials.append(mat_ref)
        card.hide_render = True
        link_obj(card)
    except Exception as e:
        print(f"Note: Reference card load skipped: {e}")


# Main build execution
def build_scene():
    print("Building Refined Tesla Model 3 (Highland) 3D Scene...")
    create_tesla_body()
    create_glass_canopy()
    create_side_windows()
    create_headlights()
    create_taillights()
    create_trims()
    create_exterior_details()
    create_wheels()
    create_interior()
    create_studio_and_lighting()
    create_studio_cameras()
    create_reference_card()
    
    blend_path = "/Users/thomasthemaker/Development/ComfySpace/playground/Blender&AI/tesla-model-3.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Scene successfully built and saved to {blend_path}")


build_scene()
