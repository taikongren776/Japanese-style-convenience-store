"""Export the diorama as a compact GLB for the interactive web viewer.

The Blender file keeps its custom toon node materials.  For export we replace
them in-memory with a glTF-compatible Principled approximation; the original
.blend is never overwritten.
"""
import bpy
import os
import math
import sys
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "dist", "scene.glb")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
scene = bpy.context.scene
# Export the closed-door pose; the web viewer drives the door itself.
scene.frame_set(1)
FX_COLLECTIONS = {"FX_RENDER_ONLY"}
EXCLUDE_TYPES = {"LIGHT", "CAMERA"}

# Deselect everything first.
for obj in bpy.context.selected_objects:
    obj.select_set(False)


def in_fx(obj):
    return any(c.name in FX_COLLECTIONS for c in obj.users_collection)


def to_linear(hex_color):
    s = (hex_color or "#888888").lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    vals = []
    for i in (0, 2, 4):
        c = int(s[i:i + 2], 16) / 255.0
        vals.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*vals, 1.0)


# Replace each material with a clean Principled setup the glTF exporter understands.
converted = {}
for mat in bpy.data.materials:
    if mat.name in converted:
        continue
    color = mat.get("vx_color", "#888888")
    kind = mat.get("vx_kind", "matte")
    alpha = float(mat.get("vx_alpha", 1.0))
    emit = float(mat.get("vx_emit", 0.0))
    rough = float(mat.get("vx_rough", 0.55))
    metal = float(mat.get("vx_metal", 0.0))
    rgb = to_linear(color)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (280, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    if "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = rough
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metal
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = alpha
    if kind in {"emissive", "decal", "softglow"}:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = max(0.2, emit)
        # Keep the diffuse base slightly dark so the glow dominates in the viewer.
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (rgb[0] * 0.2, rgb[1] * 0.2,
                                                       rgb[2] * 0.2, 1.0)
    if kind == "glass":
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = max(0.02, min(0.16, alpha))
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.08
        mat.use_backface_culling = False
    if kind == "wet":
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = min(0.45, rough)
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = max(metal, 0.15)
    if alpha < 0.999 or kind == "glass":
        try:
            mat.surface_render_method = "BLENDED"
        except Exception:
            pass
        try:
            mat.blend_method = "BLEND"
        except Exception:
            pass
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = (rgb[0], rgb[1], rgb[2], alpha)
    converted[mat.name] = True

# Select model geometry and the empty parents that carry door/bicycle transforms.
model_objects = []
for obj in scene.objects:
    if obj.type in EXCLUDE_TYPES:
        continue
    if in_fx(obj):
        continue
    if obj.type in {"MESH", "CURVE", "FONT", "EMPTY"}:
        model_objects.append(obj)

# Include parents of model objects.
parents = set()
for obj in list(model_objects):
    p = obj.parent
    while p:
        parents.add(p)
        p = p.parent
for p in parents:
    if p.type != "CAMERA" and p not in model_objects:
        model_objects.append(p)

for obj in model_objects:
    obj.hide_set(False)
    obj.select_set(True)

# Ensure active object is valid.
bpy.context.view_layer.objects.active = next((o for o in model_objects if o.type == "MESH"), None)
print("EXPORT_OBJECTS", len(model_objects),
      "meshes", sum(1 for o in model_objects if o.type == "MESH"),
      "empties", sum(1 for o in model_objects if o.type == "EMPTY"))

# Report custom-prop coverage so the viewer contract can be checked.
kinds = {}
anim = {}
for obj in model_objects:
    k = obj.get("vx_kind")
    if k:
        kinds[k] = kinds.get(k, 0) + 1
    a = obj.get("vx_anim")
    if a:
        anim[a] = anim.get(a, 0) + 1
print("EXPORT_KINDS", kinds)
print("EXPORT_ANIM", anim)
print("DOOR_ROOTS", [o.name for o in model_objects if o.name in {"DOOR_L", "DOOR_R"}])

kwargs = dict(
    filepath=OUT,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_extras=True,
    export_animations=False,
    export_cameras=False,
    export_lights=False,
    export_materials="EXPORT",
)
try:
    bpy.ops.export_scene.gltf(**kwargs)
except TypeError as e:
    print("EXPORT_KWARG_FALLBACK", e)
    kwargs.pop("export_materials", None)
    bpy.ops.export_scene.gltf(**kwargs)
print("GLB_EXPORTED", OUT, os.path.getsize(OUT) if os.path.exists(OUT) else 0)
