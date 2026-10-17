"""Reusable procedural modelling helpers for the rainy-night convenience store diorama."""
import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Euler

FONT_PATH = r"C:\Windows\Fonts\YuGothR.ttc"
FONT_BOLD_PATH = r"C:\Windows\Fonts\YuGothB.ttc"
_FONT = None
_FONT_BOLD = None
_MATS = {}
_STYLE_MATS = {}


def srgb(hex_color, alpha=1.0):
    """Convert a hex sRGB colour to Blender linear RGBA."""
    s = hex_color.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    vals = []
    for i in (0, 2, 4):
        c = int(s[i:i + 2], 16) / 255.0
        vals.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*vals, alpha)


def mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                  bpy.data.cameras, bpy.data.lights, bpy.data.collections):
        for item in list(block):
            try:
                block.remove(item)
            except Exception:
                pass


def get_font(bold=False):
    global _FONT, _FONT_BOLD
    if bold:
        if _FONT_BOLD is None:
            _FONT_BOLD = bpy.data.fonts.load(FONT_BOLD_PATH)
        return _FONT_BOLD
    if _FONT is None:
        _FONT = bpy.data.fonts.load(FONT_PATH)
    return _FONT


def new_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def link_to(obj, collection):
    if collection and collection.objects.get(obj.name) is None:
        try:
            collection.objects.link(obj)
        except RuntimeError:
            pass
    web = bpy.data.collections.get("WEB_EXPORT")
    outline = bpy.data.collections.get("OUTLINE")
    keep = {collection, web, outline}
    for c in list(obj.users_collection):
        if c not in keep:
            try:
                c.objects.unlink(obj)
            except RuntimeError:
                pass
    if web and collection is not web and obj.type in {"MESH", "CURVE", "FONT"}:
        try:
            if web.objects.get(obj.name) is None:
                web.objects.link(obj)
        except RuntimeError:
            pass


def tag(obj, outline=False, kind=None, anim=None, extra=None):
    obj["vx_outline"] = bool(outline)
    if kind:
        obj["vx_kind"] = kind
    if anim:
        obj["vx_anim"] = anim
    if extra:
        for k, v in extra.items():
            obj[k] = v
    if outline:
        outline_col = bpy.data.collections.get("OUTLINE")
        if outline_col and obj.name not in outline_col.objects:
            try:
                outline_col.objects.link(obj)
            except RuntimeError:
                pass
    return obj


def _ramp(toon):
    cr = toon.color_ramp
    cr.interpolation = "CONSTANT"
    # Build three broad bands: cool shadow, coloured mid, clean light.
    while len(cr.elements) < 3:
        cr.elements.new(0.5)
    cr.elements[0].position = 0.0
    cr.elements[1].position = 0.27
    cr.elements[2].position = 0.60
    return cr


def matte(hex_color, name=None, shadow=0.44, light=1.06, cool_shadow=True):
    key = ("matte", hex_color, round(shadow, 3), round(light, 3), cool_shadow)
    if key in _MATS:
        return _MATS[key]
    c = srgb(hex_color)
    if name is None:
        name = "TOON_" + hex_color.lstrip("#").upper()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (1, 1, 1, 1)
    s2rgb = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = _ramp(ramp)
    cool = srgb("#10203b") if cool_shadow else srgb("#080808")
    dark = tuple(c[i] * (shadow * 0.48) + cool[i] * 0.30 for i in range(3)) + (1,)
    mid = tuple(c[i] * (shadow * 1.25) + cool[i] * 0.10 for i in range(3)) + (1,)
    bright = tuple(min(1.0, c[i] * light) for i in range(3)) + (1,)
    cr.elements[0].color = dark
    cr.elements[1].color = mid
    cr.elements[2].color = bright
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0
    nt.links.new(diff.outputs["BSDF"], s2rgb.inputs["Shader"])
    nt.links.new(s2rgb.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = c
    mat["vx_color"] = hex_color
    mat["vx_kind"] = "matte"
    mat["vx_rough"] = 0.55
    mat["vx_metal"] = 0.0
    _MATS[key] = mat
    return mat


def metal(hex_color, name=None):
    key = ("metal", hex_color)
    if key in _MATS:
        return _MATS[key]
    c = srgb(hex_color)
    name = name or "METAL_" + hex_color.lstrip("#").upper()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (1, 1, 1, 1)
    s2rgb = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = _ramp(ramp)
    cr.elements[0].color = tuple(v * 0.20 for v in c[:3]) + (1,)
    cr.elements[1].color = tuple(v * 0.62 for v in c[:3]) + (1,)
    cr.elements[2].color = tuple(min(1.0, v * 1.18 + 0.08) for v in c[:3]) + (1,)
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0
    nt.links.new(diff.outputs["BSDF"], s2rgb.inputs["Shader"])
    nt.links.new(s2rgb.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = c
    mat["vx_color"] = hex_color
    mat["vx_kind"] = "matte"
    mat["vx_rough"] = 0.32
    mat["vx_metal"] = 0.55
    _MATS[key] = mat
    return mat


def emissive(hex_color, strength=3.0, name=None):
    key = ("emissive", hex_color, strength)
    if key in _MATS:
        return _MATS[key]
    c = srgb(hex_color)
    name = name or "EMIT_" + hex_color.lstrip("#").upper()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = c
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = c
    mat["vx_color"] = hex_color
    mat["vx_kind"] = "emissive"
    mat["vx_emit"] = float(strength)
    mat["vx_rough"] = 0.4
    mat["vx_metal"] = 0.0
    _MATS[key] = mat
    return mat


def glass(name="GLASS_CLEAR", tint="#bfe6ff", alpha=0.16, strength=0.0):
    key = ("glass", tint, alpha)
    if key in _MATS:
        return _MATS[key]
    c = srgb(tint)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.06
    bsdf.inputs["IOR"].default_value = 1.45
    bsdf.inputs["Alpha"].default_value = alpha
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.15
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.65
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparency_overlap = True
    mat.use_backface_culling = False
    mat.diffuse_color = c
    mat["vx_color"] = tint
    mat["vx_kind"] = "glass"
    mat["vx_alpha"] = float(alpha)
    mat["vx_emit"] = float(strength)
    mat["vx_rough"] = 0.06
    mat["vx_metal"] = 0.0
    _MATS[key] = mat
    return mat


def wet(name="WET_ASPHALT", color="#131a24", alpha=1.0, rough=0.18):
    key = ("wet", color, round(rough, 3), alpha)
    if key in _MATS:
        return _MATS[key]
    c = srgb(color)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Alpha"].default_value = alpha
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    if alpha < 1.0:
        mat.surface_render_method = "BLENDED"
    mat.diffuse_color = c
    mat["vx_color"] = color
    mat["vx_kind"] = "wet"
    mat["vx_alpha"] = float(alpha)
    mat["vx_rough"] = rough
    mat["vx_metal"] = 0.2
    _MATS[key] = mat
    return mat


def decal(hex_color, alpha=0.45, strength=2.4, name=None, additive=True):
    key = ("decal", hex_color, alpha, strength)
    if key in _MATS:
        return _MATS[key]
    c = srgb(hex_color)
    name = name or "DECAL_" + hex_color.lstrip("#").upper()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = c
    em.inputs["Strength"].default_value = strength
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixn = nt.nodes.new("ShaderNodeMixShader")
    mixn.inputs[0].default_value = alpha
    nt.links.new(trans.outputs["BSDF"], mixn.inputs[1])
    nt.links.new(em.outputs["Emission"], mixn.inputs[2])
    nt.links.new(mixn.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparency_overlap = True
    mat["vx_color"] = hex_color
    mat["vx_kind"] = "decal"
    mat["vx_alpha"] = float(alpha)
    mat["vx_emit"] = float(strength)
    mat["vx_rough"] = 0.3
    mat["vx_metal"] = 0.0
    _MATS[key] = mat
    return mat


def soft_glow(hex_color, strength=2.0, name=None, falloff=0.44):
    """A render-only radial glow/decal with a soft alpha falloff."""
    key = ("softglow", hex_color, strength, falloff)
    if key in _MATS:
        return _MATS[key]
    c = srgb(hex_color)
    name = name or "GLOW_" + hex_color.lstrip("#").upper()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    length = nt.nodes.new("ShaderNodeVectorMath")
    length.operation = "LENGTH"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "B_SPLINE"
    ramp.color_ramp.elements[0].position = 0.05
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = falloff
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = c
    em.inputs["Strength"].default_value = strength
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixn = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tc.outputs["Generated"], sub.inputs[0])
    nt.links.new(sub.outputs["Vector"], length.inputs[0])
    nt.links.new(length.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mixn.inputs[0])
    nt.links.new(trans.outputs["BSDF"], mixn.inputs[1])
    nt.links.new(em.outputs["Emission"], mixn.inputs[2])
    nt.links.new(mixn.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparency_overlap = True
    mat["vx_color"] = hex_color
    mat["vx_kind"] = "softglow"
    mat["vx_alpha"] = 0.5
    mat["vx_emit"] = float(strength)
    mat["vx_rough"] = 0.3
    mat["vx_metal"] = 0.0
    _MATS[key] = mat
    return mat


def add_bevel(obj, width=0.02, segments=2, apply=False):
    if width <= 0:
        return obj
    mod = obj.modifiers.new("SoftBevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(50)
    if apply:
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception:
            pass
    return obj


def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0, collection=None,
        outline=False, kind=None, anim=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    add_bevel(obj, bevel)
    link_to(obj, collection)
    return tag(obj, outline=outline, kind=kind or mat.get("vx_kind", "matte"), anim=anim)


def plane(name, size, loc, mat, rot=(0, 0, 0), collection=None, outline=False,
          kind=None, anim=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    link_to(obj, collection)
    return tag(obj, outline=outline, kind=kind or mat.get("vx_kind", "matte"), anim=anim)


def cylinder(name, radius, depth, loc, mat, rot=(0, 0, 0), vertices=16,
             collection=None, outline=False, bevel=0.0, kind=None, anim=None,
             radius_top=None):
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=depth,
                                        location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    add_bevel(obj, bevel)
    link_to(obj, collection)
    return tag(obj, outline=outline, kind=kind or mat.get("vx_kind", "matte"), anim=anim)


def sphere(name, radius, loc, mat, segments=20, rings=12, collection=None,
           outline=False, scale=(1, 1, 1), kind=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=radius, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    link_to(obj, collection)
    return tag(obj, outline=outline, kind=kind or mat.get("vx_kind", "matte"))


def torus(name, major, minor, loc, mat, rot=(0, 0, 0), major_seg=20,
          minor_seg=8, collection=None, outline=False):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=major_seg,
                                     minor_segments=minor_seg,
                                     location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    link_to(obj, collection)
    return tag(obj, outline=outline, kind=mat.get("vx_kind", "matte"))


def curve_tube(name, points, radius, mat, collection=None, outline=False,
               cyclic=False, resolution=8, kind=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = resolution
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    spline = cu.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = Vector(co)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, cu)
    collection.objects.link(obj) if collection else bpy.context.scene.collection.objects.link(obj)
    cu.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    link_to(obj, collection)
    return tag(obj, outline=outline, kind=kind or mat.get("vx_kind", "matte"))


def poly(name, points_xy, z, mat, collection=None, outline=False, kind=None):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [bm.verts.new((x, y, z)) for x, y in points_xy]
    bm.faces.new(verts)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj.data.materials.append(mat)
    link_to(obj, collection)
    return tag(obj, outline=outline, kind=kind or mat.get("vx_kind", "matte"))


def puddle(name, center, radius, mat, collection, seed=1, subdivisions=14,
           irregularity=0.26, z=0.012):
    rng = random.Random(seed)
    pts = []
    for i in range(subdivisions):
        a = 2 * math.pi * i / subdivisions
        r = radius * (1.0 + rng.uniform(-irregularity, irregularity))
        pts.append((center[0] + math.cos(a) * r,
                    center[1] + math.sin(a) * r * rng.uniform(0.65, 0.95)))
    return poly(name, pts, z, mat, collection=collection, kind="wet")


def text_mesh(name, text, size, loc, mat, rot=(math.pi / 2, 0, 0),
              extrude=0.008, bevel=0.0, collection=None, outline=False,
              align_x="CENTER", align_y="CENTER", bold=False, spacing=1.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = text
    cu.font = get_font(bold)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 1
    cu.align_x = align_x
    cu.align_y = align_y
    cu.space_character = spacing
    obj = bpy.data.objects.new(name, cu)
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    cu.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    link_to(obj, collection)
    return tag(obj, outline=outline, kind=mat.get("vx_kind", "matte"))


def area_light(name, loc, rot, energy, color, size, collection, shape="RECTANGLE"):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = shape
    data.size = size[0]
    data.size_y = size[1]
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def point_light(name, loc, energy, color, radius, collection, shadow=False):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius
    data.use_shadow = shadow
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = loc
    return obj


def spot_light(name, loc, rot, energy, color, size, blend, collection, shadow=True):
    data = bpy.data.lights.new(name, "SPOT")
    data.energy = energy
    data.color = color
    data.spot_size = size
    data.spot_blend = blend
    data.use_shadow = shadow
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def aim_object_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def mat_override(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def keyframe_emission(mat, frames_values, data_path='nodes["Emission"].inputs[1].default_value'):
    """Keyframe a named emission strength; used for render/Blender animation."""
    if not mat or not mat.use_nodes:
        return
    node = mat.node_tree.nodes.get("Emission")
    if not node:
        for n in mat.node_tree.nodes:
            if n.type == "EMISSION":
                node = n
                break
    if not node:
        return
    for frame, val in frames_values:
        node.inputs[1].default_value = val
        node.inputs[1].keyframe_insert("default_value", frame=frame)
