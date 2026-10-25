"""Build a food-styled sandwich scene from sandwich-reference.png.

Run through MCP for Blender's execute_blender_code tool.
"""

import bpy
import math
import random
from mathutils import Vector

random.seed(27)
ROOT = "/Users/thomasthemaker/Development/ComfySpace/playground/Blender&AI"

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.engine = "BLENDER_EEVEE"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.film_transparent = False
scene.world.color = (0.28, 0.25, 0.22)


def mat(name, color, roughness=0.7, metallic=0.0, noise=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if noise:
        tex = m.node_tree.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise[0]
        tex.inputs["Detail"].default_value = 3
        ramp = m.node_tree.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.23
        ramp.color_ramp.elements[0].color = (*noise[1], 1)
        ramp.color_ramp.elements[1].position = 0.77
        ramp.color_ramp.elements[1].color = (*noise[2], 1)
        m.node_tree.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        m.node_tree.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        bump = m.node_tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.15
        bump.inputs["Distance"].default_value = 0.015
        m.node_tree.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        m.node_tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


crumb = mat("sourdough crumb - airy", (0.75, 0.57, 0.34), noise=(24, (0.34, 0.21, 0.10), (0.72, 0.52, 0.29)))
crust = mat("crackly dark crust", (0.28, 0.11, 0.043), noise=(20, (0.08, 0.025, 0.008), (0.57, 0.27, 0.075)))
toast = mat("golden toasted face", (0.67, 0.35, 0.11), noise=(13, (0.08, 0.025, 0.006), (0.48, 0.21, 0.065)))
flour = mat("dusting of flour", (0.85, 0.75, 0.60), roughness=0.95)
turkey = mat("roast turkey", (0.89, 0.65, 0.50), roughness=0.75, noise=(18, (0.74, 0.43, 0.32), (0.97, 0.80, 0.65)))
turkey_edge = mat("turkey roasted edge", (0.57, 0.29, 0.19))
tomato = mat("ripe tomato flesh", (0.84, 0.13, 0.08), roughness=0.37, noise=(8, (0.58, 0.055, 0.032), (0.95, 0.24, 0.14)))
tomato_seed = mat("tomato seeds", (0.95, 0.76, 0.27), roughness=0.33)
lettuce = mat("butter lettuce", (0.39, 0.63, 0.08), roughness=0.55, noise=(12, (0.20, 0.42, 0.026), (0.61, 0.80, 0.14)))
lettuce_edge = mat("lettuce pale tips", (0.66, 0.82, 0.19), roughness=0.6)
bacon = mat("crispy bacon", (0.43, 0.105, 0.055), roughness=0.34, noise=(16, (0.19, 0.035, 0.015), (0.72, 0.26, 0.11)))
bacon_fat = mat("bacon fat", (0.86, 0.54, 0.31), roughness=0.28)
cheese = mat("melted cheddar", (0.93, 0.70, 0.31), roughness=0.3)
aioli = mat("lemon aioli", (0.94, 0.88, 0.61), roughness=0.34)
herb = mat("aioli herbs", (0.20, 0.32, 0.10), roughness=0.65)
table = mat("warm stone tabletop", (0.43, 0.37, 0.31), roughness=0.9, noise=(4, (0.34, 0.29, 0.25), (0.54, 0.47, 0.40)))


def mesh_obj(name, verts, faces, material, bevel=0):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth = True
    if bevel:
        mod = obj.modifiers.new("soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def ball(name, loc, scale, material, segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o


def ribbon(name, x0, x1, y, z, width, amp, material, n=32, seed=0):
    verts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        wave = amp * (math.sin(t * 9 * math.pi + seed) + 0.4 * math.sin(t * 17 * math.pi + seed))
        for sign in (-1, 1):
            yy = y + sign * width * (0.5 + 0.08 * math.sin(t * 13 + seed))
            verts.append((x, yy, z + wave + sign * amp * 0.4 * math.sin(t * 12 + seed)))
    faces = [(2*i, 2*i+1, 2*i+3, 2*i+2) for i in range(n)]
    o = mesh_obj(name, verts, faces, material)
    sol = o.modifiers.new("thin soft sheet", "SOLIDIFY")
    sol.thickness = 0.025
    sol.offset = 0
    return o


def bread(name, z0, thickness, seed):
    rng = random.Random(seed)
    # Oval-ish artisan loaf slice with four broad sides and an irregular edge.
    n = 64
    outline = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        # Superellipse rounds a rectangle while preserving broad side faces.
        x = 1.68 * math.copysign(abs(c) ** 0.42, c)
        y = 1.10 * math.copysign(abs(s) ** 0.42, s)
        irregular = 1 + 0.025 * math.sin(5*a + seed) + 0.015 * math.sin(11*a + seed)
        outline.append((x * irregular, y * irregular))
    verts = [(x, y, z0) for x,y in outline] + [(x, y, z0+thickness) for x,y in outline]
    verts += [(0,0,z0),(0,0,z0+thickness)]
    faces = []
    for i in range(n):
        j = (i+1)%n
        faces.extend([(i,j,2*n), (n+i,2*n+1,n+j), (i,n+i,n+j,j)])
    core = mesh_obj(name + " airy crumb", verts, faces, crumb, bevel=0.035)
    # Crust bands at the upper and lower edge, leaving a cream porous side wall.
    for label, zc, h in (("bottom crust",z0+0.045,0.09),("top crust",z0+thickness-0.045,0.09)):
        vv=[]
        for x,y in outline:
            for dz in (-h/2,h/2):
                vv.append((x*1.018,y*1.018,zc+dz))
        ff=[(2*i,2*((i+1)%n),2*((i+1)%n)+1,2*i+1) for i in range(n)]
        mesh_obj(name+" "+label,vv,ff,crust)
    # Toast face facing camera for top bread and hidden filling face for bottom.
    facez = z0+thickness+0.003
    facev = [(x*0.95,y*0.95,facez) for x,y in outline]+[(0,0,facez+0.003)]
    facef = [(i,(i+1)%n,n) for i in range(n)]
    mesh_obj(name+" toasted surface",facev,facef,toast)
    # Porous crumb seen on the front cut face. Small inset toasted cavities.
    for k in range(65):
        x = rng.uniform(-1.52,1.52)
        zz = rng.uniform(z0+0.10,z0+thickness-0.09)
        radius = rng.uniform(0.018,0.067)
        ball(name+" crumb pore",(x,-1.104,zz),(radius,0.005,radius*rng.uniform(0.55,1.3)),toast,8,4)
    if name.startswith("Top"):
        for k in range(80):
            x = rng.uniform(-1.55,1.55)
            y = rng.uniform(-0.98,0.98)
            ball("flour fleck",(x,y,facez+0.008),(0.007,0.011,0.003),flour,6,3)
    return core


# Ground and bottom slice.
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-0.07))
bpy.context.object.name = "studio tabletop"
bpy.context.object.data.materials.append(table)
bread("Bottom sourdough",0.00,0.40,4)

# Aioli: overlapping metaballs form one soft uneven ribbon along the front edge.
mb = bpy.data.metaballs.new('aioli melted ribbon'); mb.resolution=0.12; mb.render_resolution=0.06
mo = bpy.data.objects.new('lemon aioli - continuous',mb); scene.collection.objects.link(mo)
mo.data.materials.append(aioli)
for i in range(23):
    x = -1.57 + i*0.143
    y = -1.03 + 0.025*math.sin(i*1.5)
    el=mb.elements.new(); el.co=(x,y,0.43); el.radius=0.13; el.stiffness=2
for i in range(75):
    ball("herb in aioli",(random.uniform(-1.58,1.58),-1.112,random.uniform(0.42,0.47)),(0.008,0.003,0.006),herb,6,3)

# Turkey: thin layered, freely folded slices with lightly browned edges.
for j in range(6):
    y = -0.86 + j*0.33
    z = 0.54 + j*0.045
    ribbon("folded roast turkey %02d"%j,-1.62,1.63,y,z,0.36,0.085,turkey,40,j*1.3)
    ribbon("roasted turkey edge %02d"%j,-1.60,1.60,y-0.18,z+0.018,0.020,0.06,turkey_edge,32,j*1.3)

# Tomato slices span the sandwich, with darker juicy rims and visible seed glints.
for j,x in enumerate((-1.02,-0.35,0.35,1.02)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.53, depth=0.125, location=(x,-0.31,0.90))
    o=bpy.context.object; o.name="ripe tomato slice %d"%j
    o.scale.y=1.45; o.data.materials.append(tomato)
    bevel=o.modifiers.new("juicy rounded edge","BEVEL"); bevel.width=0.025; bevel.segments=3
    o.modifiers.new("weighted normals","WEIGHTED_NORMAL")
    for k in range(5):
        a=(k+0.5)*2*math.pi/5
        ball("tomato seed",(x+0.28*math.cos(a),-0.31+0.38*math.sin(a),0.971),(0.028,0.04,0.009),tomato_seed,8,4)

# Frilled lettuce leaves made from radially ruffled sheet meshes.
def leaf(index,cx,cy,angle):
    n=30; rows=7; verts=[]
    for ir in range(rows):
        r=ir/(rows-1)
        for i in range(n+1):
            t=i/n
            a=angle+(t-0.5)*1.65
            reach=0.18+0.78*r
            x=cx+reach*math.cos(a)
            y=cy+reach*math.sin(a)
            z=1.005+0.075*r+0.04*r*math.sin(t*12*math.pi+index)
            verts.append((x,y,z))
    faces=[]
    for ir in range(rows-1):
        for i in range(n):
            a=ir*(n+1)+i; b=a+n+1
            faces.append((a,b,b+1,a+1))
    o=mesh_obj("butter lettuce leaf %02d"%index,verts,faces,lettuce)
    solid=o.modifiers.new("leaf thickness","SOLIDIFY"); solid.thickness=0.012
    return o

for i,(x,y,a) in enumerate(((-0.9,-0.25,-1.2),(0.1,-0.27,-1.65),(0.95,-0.22,-1.95),(-1.0,0.22,2.6),(0.0,0.18,1.8),(1.0,0.15,0.3))):
    leaf(i,x,y,a)

# Three curling bacon strips with contrasting streaks of crisp fat.
for i,y in enumerate((-0.72,-0.12,0.48)):
    ribbon("crispy bacon strip %d"%i,-1.77,1.78,y,1.21,0.21,0.07,bacon,48,i*2.0)
    ribbon("bacon fat streak %d"%i,-1.73,1.74,y+0.03,1.225,0.04,0.055,bacon_fat,48,i*2.0)

# Soft melted cheese, visible as a folded sheet and a few drips down front.
ribbon("melted cheddar sheet",-1.59,1.58,0,1.31,1.13,0.035,cheese,42,0.4)
ribbon("cheddar visible at front",-1.54,1.54,-1.07,1.29,0.08,0.027,cheese,40,0.3)

bread("Top sourdough",1.31,0.39,9)

# Reference sheet stays in the .blend and appears to the right in viewport,
# but does not render in the food photograph.
ref=bpy.data.images.load(ROOT+"/sandwich-reference.png",check_existing=True)
ref.pack()
bpy.ops.object.empty_add(type="IMAGE",location=(4.7,0,1.55))
refobj=bpy.context.object; refobj.name="REFERENCE - four sandwich views"
refobj.data=ref; refobj.empty_display_size=3.5; refobj.hide_render=True

# Studio lighting and view cameras.
def target(obj,point):
    obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()

def area(name,loc,power,size):
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape='DISK'; data.size=size
    obj=bpy.data.objects.new(name,data); scene.collection.objects.link(obj); obj.location=loc
    target(obj,(0,0,1)); return obj

area("large softbox key",(0,-4,7),850,5)
area("warm rim",(3,3,5),620,4)
area("front fill",(-4,-1,3),330,4)

def camera(name,loc,ortho):
    data=bpy.data.cameras.new(name); obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj); obj.location=loc
    target(obj,(0,0,0.95)); data.type='ORTHO'; data.ortho_scale=ortho
    data.lens=55; return obj

cams={
    "hero":camera("Camera - hero",(4.4,-6.9,4.5),5.15),
    "front":camera("Camera - front",(0,-8,2.55),4.6),
    "side":camera("Camera - side",(8,0,2.65),4.7),
    "top":camera("Camera - top",(0,-0.02,9),4.8),
}
scene.camera=cams["hero"]

# Select the sandwich for an immediately useful opening view.
bpy.ops.object.select_all(action='DESELECT')
base=bpy.data.objects.get("Bottom sourdough airy crumb")
base.select_set(True); bpy.context.view_layer.objects.active=base
for area_ in bpy.context.screen.areas:
    if area_.type=='VIEW_3D':
        area_.spaces.active.region_3d.view_distance=7
        area_.spaces.active.region_3d.view_location=(0,0,0.95)

bpy.ops.wm.save_as_mainfile(filepath=ROOT+"/sandwich-study.blend")
print("SANDWICH_SCENE_READY",len(scene.objects),bpy.data.filepath)
