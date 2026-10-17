"""Build the rainy-night Hoshiakari Mart diorama from scratch in Blender."""
import bpy
import math
import os
import random
import sys

from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

from scene_lib import (  # noqa: E402
    clear_scene, new_collection, srgb, matte, metal, emissive, glass, wet, decal,
    soft_glow, box, plane, cylinder, sphere, torus, curve_tube, poly, puddle,
    text_mesh, area_light, point_light, spot_light, aim_object_at,
    tag, mat_override, box as make_box, keyframe_emission,
)

BLEND_PATH = os.path.join(ROOT, "HoshiakariMart_RainyNight.blend")
RNG = random.Random(20261017)

# ---------------------------------------------------------------------------
# Palette + layout constants
# ---------------------------------------------------------------------------
INK = "#172033"
CREAM = "#efe6d3"
PAPER = "#f7f2e7"
WHITE = "#f4f3ec"
WARM = "#ffcf8a"
AMBER = "#ffb45d"
ORANGE = "#f29a55"
MINT = "#9bdbc9"
MINT_DARK = "#4d998e"
TEAL = "#2b6d6b"
RED = "#c34f4f"
PINK = "#ee7199"
CYAN = "#80e4f0"
BLUE = "#6aa4d8"
STEEL = "#78818a"
DARKSTEEL = "#38424e"
ASPHALT = "#171d26"
SIDEWALK = "#646a70"
CONCRETE = "#8a8a82"
WOOD = "#6b4b39"

BASE_HALF = 3.6
WALK_Z = 0.14

# Start from an empty file before building module-level collections/materials.
clear_scene()

STORE_X0, STORE_X1 = -0.35, 2.65
STORE_Y0, STORE_Y1 = -0.75, 1.85
CHAMFER = 0.72
GLASS_BOTTOM = 0.22
GLASS_TOP = 2.43
CEILING_Z = 2.56
ROOF_Z = 2.94
CANOPY_Z = 2.48
SIGN_Z = 3.38

BASE = new_collection("BASE")
STREET = new_collection("STREET")
STORE = new_collection("STORE_EXTERIOR")
INTERIOR = new_collection("STORE_INTERIOR")
DETAIL = new_collection("STORE_DETAIL")
PROPS = new_collection("STREET_PROPS")
NEIGHBOR = new_collection("NEIGHBORHOOD")
ALLEY = new_collection("ALLEY")
FX = new_collection("FX_RENDER_ONLY")
LIGHTS = new_collection("LIGHTS")
CAMCOL = new_collection("CAMERA")
OUTLINE = new_collection("OUTLINE")
WEB = new_collection("WEB_EXPORT")
OUTLINE.color_tag = "COLOR_04"
FX.hide_render = False

# Material palette
MAT = {
    "ink": matte(INK),
    "cream": matte(CREAM),
    "paper": matte(PAPER),
    "white": matte(WHITE),
    "warm": matte("#d9b88a"),
    "amber": matte("#b9783d"),
    "orange": matte(ORANGE),
    "mint": matte(MINT),
    "mint_dark": matte(MINT_DARK),
    "teal": matte(TEAL),
    "red": matte(RED),
    "pink": matte(PINK),
    "cyan": matte(CYAN),
    "blue": matte(BLUE),
    "steel": metal(STEEL),
    "darksteel": metal(DARKSTEEL),
    "asphalt": wet("WET_ASPHALT", ASPHALT, 1.0, 0.16),
    "sidewalk": wet("WET_SIDEWALK", SIDEWALK, 1.0, 0.30),
    "concrete": matte(CONCRETE),
    "wood": matte(WOOD),
    "glass": glass("GLASS_STORE", "#d9f3ff", 0.025),
    "glass_warm": glass("GLASS_WARM", "#ffe1b8", 0.04),
    "puddle": wet("PUDDLE", "#0c1622", 0.66, 0.045),
    "paint": matte("#d9d8ce"),
}


def outline(obj):
    return tag(obj, outline=True, kind=obj.get("vx_kind", "matte"))


# ---------------------------------------------------------------------------
# Base and streets
# ---------------------------------------------------------------------------
def build_base():
    # Main display plinth: dark lacquer with a thin brass band and a square top.
    box("Base_Plinth", (7.42, 7.42, 0.34), (0, 0, -0.27), matte("#10141c"),
        bevel=0.07, collection=BASE, outline=True)
    box("Base_BrassBand", (7.46, 7.46, 0.026), (0, 0, -0.095),
        metal("#a88455"), bevel=0.006, collection=BASE)
    box("Base_TopPlate", (7.22, 7.22, 0.06), (0, 0, -0.035),
        matte("#171b22"), bevel=0.018, collection=BASE, outline=True)
    box("Base_Asphalt", (7.18, 7.18, 0.05), (0, 0, 0.005),
        MAT["asphalt"], bevel=0.015, collection=BASE)
    # Sidewalk is a raised L-shaped slab; two overlapping boxes keep the corner crisp.
    box("Sidewalk_Main", (5.55, 5.55, WALK_Z), (0.78, 0.78, WALK_Z / 2 + 0.02),
        MAT["sidewalk"], bevel=0.012, collection=STREET, outline=True)
    # Thin warmer tiles on the sidewalk.
    for i in range(12):
        x = -1.75 + (i % 6) * 0.9
        y = -1.6 + (i // 6) * 1.6
        plane(f"Sidewalk_Patch_{i:02d}", (0.78, 0.16), (x, y, WALK_Z + 0.023),
              matte("#70767b"), collection=STREET)
    # Curb rails around the sidewalk.
    box("Curb_Front", (5.55, 0.13, 0.16), (0.78, -2.0, 0.10),
        matte("#97968d"), bevel=0.022, collection=STREET, outline=True)
    box("Curb_Left", (0.13, 5.55, 0.16), (-2.0, 0.78, 0.10),
        matte("#97968d"), bevel=0.022, collection=STREET, outline=True)
    # Brass pinstripe inset around the top plate.
    for name, size, loc in (
        ("Pin_Front", (7.3, 0.018, 0.012), (0, -3.56, 0.003)),
        ("Pin_Back", (7.3, 0.018, 0.012), (0, 3.56, 0.003)),
        ("Pin_Left", (0.018, 7.3, 0.012), (-3.56, 0, 0.003)),
        ("Pin_Right", (0.018, 7.3, 0.012), (3.56, 0, 0.003)),
    ):
        box(name, size, loc, metal("#8a6d45"), collection=BASE)
    # Front plaque.
    box("Plaque_Base", (1.5, 0.035, 0.23), (0.25, -3.735, -0.20),
        metal("#8c6f47"), bevel=0.014, collection=BASE)
    text_mesh("Plaque_Text", "星あかりマート  ·  RAINY NIGHT 23:47", 0.072,
              (0.25, -3.758, -0.205), metal("#d2b988"), extrude=0.002,
              collection=BASE, align_x="CENTER")


def build_street():
    # Lane dashes on the front and left road.
    for i, x in enumerate((-3.2, -2.5, -1.8, -1.1, -0.4, 0.3, 1.0, 1.7, 2.4, 3.1)):
        plane(f"Lane_Front_{i}", (0.36, 0.035), (x, -2.98, 0.032),
              MAT["paint"], collection=STREET)
    for i, y in enumerate((-3.2, -2.5, -1.8, -1.1, -0.4, 0.3, 1.0, 1.7, 2.4, 3.1)):
        plane(f"Lane_Left_{i}", (0.035, 0.36), (-2.98, y, 0.032),
              MAT["paint"], collection=STREET)
    # Crosswalk crossing the front road, and its sibling on the left road.
    for i in range(7):
        x = -3.05 + i * 0.25
        plane(f"Zebra_Front_{i}", (0.20, 1.22), (x, -2.77, 0.035),
              matte("#e7e4d8"), collection=STREET)
    for i in range(7):
        y = -3.05 + i * 0.25
        plane(f"Zebra_Left_{i}", (1.22, 0.20), (-2.77, y, 0.035),
              matte("#e7e4d8"), collection=STREET)
    # Parking bay in front of the shop.
    y_bay = -2.10
    for i, (name, sx, sy, x, y) in enumerate((
        ("Park_Line_Top", 2.05, 0.035, 1.83, -3.34),
        ("Park_Line_Bottom", 2.05, 0.035, 1.83, -2.14),
        ("Park_Line_Left", 0.035, 1.22, 0.82, -2.74),
        ("Park_Line_Right", 0.035, 1.22, 2.84, -2.74),
    )):
        plane(name, (sx, sy), (x, y, 0.036), matte("#ded9c9"), collection=STREET)
    for i in range(3):
        box(f"WheelStop_{i}", (0.38, 0.12, 0.08), (1.15 + i * 0.55, -2.26, 0.06),
            MAT["concrete"], bevel=0.02, collection=STREET)
    text_mesh("Parking_P", "P", 0.42, (2.55, -2.72, 0.045), matte("#dad5c8"),
              rot=(0, 0, 0), extrude=0.001, collection=STREET)
    # Tactile paving from the crossing to the entrance.
    for i in range(8):
        x = -1.55 + i * 0.32
        plane(f"Tactile_{i}", (0.25, 0.30), (x, -1.88 + i * 0.12, WALK_Z + 0.025),
              matte("#b99d4d"), collection=STREET)
    # Manhole cover.
    cylinder("Manhole", 0.31, 0.018, (1.15, -2.70, 0.034), metal("#5d6266"),
             collection=STREET, vertices=28)
    torus("Manhole_Ring", 0.22, 0.007, (1.15, -2.70, 0.045), metal("#3e4449"),
          collection=STREET, major_seg=28, minor_seg=5)
    # Drain grates along the curbs.
    for i, (x, y, rotz) in enumerate((
        (-0.9, -2.035, 0.0), (1.65, -2.035, 0.0), (-2.035, 1.35, math.pi / 2)
    )):
        box(f"Drain_{i}", (0.60, 0.20, 0.025), (x, y, 0.105),
            MAT["darksteel"], bevel=0.006, collection=STREET)
        for j in range(5):
            if rotz == 0:
                box(f"Drain_Slat_{i}_{j}", (0.045, 0.17, 0.012),
                    (x - 0.22 + j * 0.11, y, 0.121), MAT["steel"],
                    collection=STREET)
            else:
                box(f"Drain_Slat_{i}_{j}", (0.17, 0.045, 0.012),
                    (x, y - 0.22 + j * 0.11, 0.121), MAT["steel"],
                    collection=STREET)
    # Puddles + wet patches.
    puddle("Puddle_Road_1", (0.2, -2.75), 0.83, MAT["puddle"], STREET, seed=11,
           subdivisions=22, irregularity=0.24, z=0.033)
    puddle("Puddle_Road_2", (-1.55, -2.05), 0.46, MAT["puddle"], STREET, seed=17,
           subdivisions=18, irregularity=0.30, z=0.034)
    puddle("Puddle_Sidewalk_1", (0.55, -1.28), 0.47, MAT["puddle"], STREET,
           seed=23, subdivisions=18, irregularity=0.32, z=WALK_Z + 0.028)
    puddle("Puddle_Sidewalk_2", (1.95, -0.95), 0.32, MAT["puddle"], STREET,
           seed=29, subdivisions=16, irregularity=0.28, z=WALK_Z + 0.028)
    puddle("Puddle_Alley", (2.95, 0.6), 0.30, MAT["puddle"], ALLEY, seed=31,
           subdivisions=16, z=WALK_Z + 0.026)
    # Painted reflection slicks under the shop lights.
    reflections = [
        (0.45, -1.55, 1.35, 0.05, "#ffce8c", 0.18),
        (1.4, -1.80, 1.70, 0.055, "#ffbb77", 0.16),
        (2.35, -1.65, 0.85, 0.045, "#ffd699", 0.14),
        (1.15, -2.33, 1.35, 0.06, "#ffd08a", 0.12),
        (-0.92, -1.88, 0.55, 0.035, "#8feaff", 0.19),
        (-1.25, -2.28, 0.95, 0.045, "#8feaff", 0.15),
        (2.45, -0.55, 0.5, 0.035, "#ff8ea9", 0.12),
    ]
    for i, (x, y, length, width, col, alpha) in enumerate(reflections):
        pts = []
        for k in range(7):
            yy = y - length / 2 + length * k / 6
            w = width * (0.45 + 0.55 * (1 - abs(k - 3) / 3)) * RNG.uniform(0.7, 1.3)
            pts.append((x - w, yy))
        for k in range(6, -1, -1):
            yy = y - length / 2 + length * k / 6
            w = width * (0.45 + 0.55 * (1 - abs(k - 3) / 3)) * RNG.uniform(0.7, 1.3)
            pts.append((x + w, yy))
        poly(f"LightSlick_{i}", pts, 0.041, decal(col, alpha=alpha, strength=2.0),
             collection=FX)
    # Fine ripple rings on the puddles.
    ripple_spots = [
        (0.1, -2.75, 0.18), (0.55, -2.7, 0.11), (-0.3, -2.6, 0.10),
        (-1.55, -2.05, 0.13), (0.45, -1.32, 0.10), (0.72, -1.2, 0.075),
        (1.95, -0.97, 0.09), (2.95, 0.6, 0.08), (1.9, -2.55, 0.10),
    ]
    for i, (x, y, r) in enumerate(ripple_spots):
        torus(f"PuddleRipple_{i}", r, 0.008, (x, y, WALK_Z + 0.031 if y > -2.0 else 0.043),
              decal("#d7f7ff", alpha=0.25, strength=1.0), collection=FX,
              major_seg=18, minor_seg=4)


# ---------------------------------------------------------------------------
# Store shell, glass facade, canopy, signage
# ---------------------------------------------------------------------------
def build_store_outer():
    # Plinth / step
    box("Store_Plinth", (3.19, 2.78, 0.15), (1.15, 0.55, 0.24),
        matte("#5f625f"), bevel=0.028, collection=STORE, outline=True)
    box("Store_Floor", (3.02, 2.62, 0.07), (1.15, 0.55, 0.235),
        matte("#cfc9bc"), bevel=0.01, collection=INTERIOR)
    # Back and right opaque walls
    box("Wall_Back", (3.05, 0.13, 2.60), (1.15, STORE_Y1 - 0.02, 1.46),
        MAT["cream"], bevel=0.025, collection=STORE, outline=True)
    box("Wall_Right", (0.13, 2.62, 2.60), (STORE_X1 + 0.02, 0.55, 1.46),
        MAT["cream"], bevel=0.025, collection=STORE, outline=True)
    # Interior lining echoes the warm white interior.
    box("Wall_Back_Lining", (3.0, 0.04, 2.30), (1.13, STORE_Y1 - 0.11, 1.38),
        matte("#dfcfb4"), collection=INTERIOR)
    box("Wall_Right_Lining", (0.04, 2.42, 2.30), (STORE_X1 - 0.09, 0.55, 1.38),
        matte("#dfcfb4"), collection=INTERIOR)
    # Interior ceiling, light panels and roof.
    plane("Ceiling", (3.0, 2.6), (1.15, 0.55, CEILING_Z),
          matte("#cdbda3"), rot=(0, 0, 0), collection=INTERIOR)
    box("Roof_Slab", (3.18, 2.74, 0.19), (1.15, 0.55, ROOF_Z - 0.06),
        MAT["cream"], bevel=0.035, collection=STORE, outline=True)
    box("Roof_Parapet_Front", (3.20, 0.10, 0.28), (1.15, STORE_Y0 - 0.06, ROOF_Z + 0.07),
        MAT["cream"], bevel=0.025, collection=STORE, outline=True)
    box("Roof_Parapet_Right", (0.10, 2.72, 0.28), (STORE_X1 + 0.05, 0.55, ROOF_Z + 0.07),
        MAT["cream"], bevel=0.02, collection=STORE, outline=True)
    # Roof service units.
    make_aircon("AC_Roof_1", (0.55, 1.2, ROOF_Z + 0.17), 0.0, scale=1.0, collection=STORE)
    make_aircon("AC_Roof_2", (1.8, 1.25, ROOF_Z + 0.17), math.pi, scale=0.9, collection=STORE)
    cylinder("Roof_Vent_1", 0.08, 0.55, (0.1, 0.8, ROOF_Z + 0.28),
             MAT["steel"], collection=STORE, vertices=12)
    cylinder("Roof_Vent_2", 0.06, 0.35, (2.15, 0.9, ROOF_Z + 0.18),
             MAT["steel"], collection=STORE, vertices=12)
    # Chamfered glazing frame corner posts.
    posts = [
        (STORE_X0 + CHAMFER, STORE_Y0), (STORE_X0, STORE_Y0 + CHAMFER),
        (STORE_X1, STORE_Y0), (STORE_X0, STORE_Y1 - 0.04),
    ]
    for i, (x, y) in enumerate(posts):
        box(f"Facade_CornerPost_{i}", (0.085, 0.085, 2.28),
            (x, y, (GLASS_BOTTOM + GLASS_TOP) / 2),
            MAT["teal"], bevel=0.012, collection=STORE, outline=True)
    # Front and left glass fields.
    front_mid = ((STORE_X0 + CHAMFER + STORE_X1) / 2, STORE_Y0 - 0.005)
    plane("Glass_Front", (STORE_X1 - (STORE_X0 + CHAMFER), GLASS_TOP - GLASS_BOTTOM),
          (front_mid[0], front_mid[1], (GLASS_TOP + GLASS_BOTTOM) / 2),
          MAT["glass"], rot=(math.pi / 2, 0, 0), collection=STORE)
    left_mid = (STORE_X0 - 0.005, (STORE_Y0 + CHAMFER + STORE_Y1) / 2)
    plane("Glass_Left", (STORE_Y1 - (STORE_Y0 + CHAMFER), GLASS_TOP - GLASS_BOTTOM),
          (left_mid[0], left_mid[1], (GLASS_TOP + GLASS_BOTTOM) / 2),
          MAT["glass"], rot=(math.pi / 2, 0, -math.pi / 2), collection=STORE)
    # Mullions / rails.
    for i, x in enumerate((STORE_X0 + CHAMFER + 1.16, STORE_X1 - 0.06)):
        box(f"Mullion_Front_{i}", (0.040, 0.06, 2.22),
            (x, STORE_Y0 - 0.005, 1.35), MAT["teal"], bevel=0.006,
            collection=STORE, outline=True)
    for i, y in enumerate((STORE_Y0 + CHAMFER + 1.20, STORE_Y1 - 0.06)):
        box(f"Mullion_Left_{i}", (0.06, 0.040, 2.22),
            (STORE_X0 - 0.005, y, 1.35), MAT["teal"], bevel=0.006,
            collection=STORE, outline=True)
    box("Facade_Rail_Bottom", (STORE_X1 - STORE_X0 - 0.55, 0.08, 0.08),
        ((STORE_X0 + STORE_X1 + 0.55) / 2 - 0.03, STORE_Y0 - 0.005, 0.245),
        MAT["teal"], bevel=0.009, collection=STORE, outline=True)
    box("Facade_Rail_Top", (STORE_X1 - STORE_X0 - 0.55, 0.08, 0.075),
        ((STORE_X0 + STORE_X1 + 0.55) / 2 - 0.03, STORE_Y0 - 0.005, GLASS_TOP - 0.03),
        MAT["teal"], bevel=0.008, collection=STORE, outline=True)
    box("Facade_Rail_Left_Bottom", (0.08, STORE_Y1 - STORE_Y0 - 0.55, 0.08),
        (STORE_X0 - 0.005, (STORE_Y0 + STORE_Y1 + 0.55) / 2,
         0.245), MAT["teal"], bevel=0.009, collection=STORE, outline=True)
    box("Facade_Rail_Left_Top", (0.08, STORE_Y1 - STORE_Y0 - 0.55, 0.075),
        (STORE_X0 - 0.005, (STORE_Y0 + STORE_Y1 + 0.55) / 2,
         GLASS_TOP - 0.03), MAT["teal"], bevel=0.008, collection=STORE, outline=True)
    # Fascia face above the glazing.
    fascia_mat = matte("#a9cbbd")
    box("Fascia_Front", (STORE_X1 - (STORE_X0 + CHAMFER), 0.18, 0.54),
        ((STORE_X0 + CHAMFER + STORE_X1) / 2, STORE_Y0 - 0.02, 2.72),
        fascia_mat, bevel=0.02, collection=STORE, outline=True)
    box("Fascia_Left", (0.18, STORE_Y1 - (STORE_Y0 + CHAMFER), 0.54),
        (STORE_X0 - 0.02, (STORE_Y0 + CHAMFER + STORE_Y1) / 2, 2.72),
        fascia_mat, bevel=0.02, collection=STORE, outline=True)
    box("Fascia_Corner", (0.88, 0.88, 0.54), (STORE_X0 + 0.32, STORE_Y0 + 0.02, 2.72),
        fascia_mat, rot=(0, 0, -math.pi / 4), bevel=0.02, collection=STORE,
        outline=True)
    box("Fascia_OrangeStripe", (2.36, 0.02, 0.035),
        (1.50, STORE_Y0 - 0.116, 2.52), emissive("#f19a58", 1.2),
        collection=STORE)
    box("Fascia_MintStripe", (2.36, 0.02, 0.025),
        (1.50, STORE_Y0 - 0.116, 2.49), emissive("#9af0d6", 1.0),
        collection=STORE)
    # Roof sign cabinet over the front.
    box("Sign_Cabinet", (2.52, 0.25, 0.86), (1.47, STORE_Y0 - 0.15, SIGN_Z + 0.20),
        matte("#19362f"), bevel=0.035, collection=STORE, outline=True)
    box("Sign_LightFace", (2.33, 0.045, 0.67), (1.47, STORE_Y0 - 0.29, SIGN_Z + 0.20),
        emissive("#fff2cf", 1.8), bevel=0.012, collection=STORE)
    # Star mark and Japanese brand sign; both are real meshes, so the GLB keeps them.
    star_points = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        r = 0.18 if i % 2 == 0 else 0.075
        star_points.append((0.34 + math.cos(a) * r, 0.55 + math.sin(a) * r))
    poly("Sign_Star", star_points, STORE_Y0 - 0.318, emissive("#f29a55", 2.4),
         collection=STORE)
    box("Sign_Star_Stem", (0.22, 0.012, 0.035), (0.34, STORE_Y0 - 0.319, 0.31),
        emissive("#f29a55", 2.2), collection=STORE)
    text_mesh("Sign_Brand_JP", "星あかりマート", 0.285,
              (1.53, STORE_Y0 - 0.325, SIGN_Z + 0.36), matte("#24534c"),
              rot=(math.pi / 2, 0, 0), extrude=0.012, collection=STORE,
              bold=True)
    text_mesh("Sign_Brand_EN", "HOSHIAKARI MART", 0.105,
              (1.53, STORE_Y0 - 0.328, SIGN_Z + 0.03), matte("#326b61"),
              rot=(math.pi / 2, 0, 0), extrude=0.004, collection=STORE,
              spacing=1.1)
    text_mesh("Sign_Tagline", "24H  ·  ATM  ·  COFFEE  ·  HOT FOOD", 0.052,
              (1.53, STORE_Y0 - 0.330, SIGN_Z - 0.14), matte("#b06d35"),
              rot=(math.pi / 2, 0, 0), extrude=0.002, collection=STORE)
    # Side fascia sign facing the left street.
    box("Sign_Left_Cabinet", (0.13, 1.36, 0.56), (STORE_X0 - 0.10, 0.86, 2.72),
        matte("#19362f"), bevel=0.022, collection=STORE, outline=True)
    box("Sign_Left_Face", (0.04, 1.24, 0.44), (STORE_X0 - 0.18, 0.86, 2.72),
        emissive("#fff0c9", 1.35), collection=STORE)
    text_mesh("Sign_Left_Text", "星あかり  24H", 0.115,
              (STORE_X0 - 0.225, 0.86, 2.72), matte("#24534c"),
              rot=(math.pi / 2, 0, -math.pi / 2), extrude=0.004,
              collection=STORE, bold=True)
    # Perpendicular blade sign at the corner (visible from the street).
    box("Blade_Arm", (0.38, 0.07, 0.07), (-0.02, -0.84, 2.96),
        MAT["darksteel"], collection=STORE, outline=True)
    box("Blade_Sign", (0.65, 0.10, 0.60), (0.16, -0.96, 2.66),
        matte("#2a2233"), rot=(0, 0, math.radians(12)), bevel=0.02,
        collection=STORE, outline=True)
    box("Blade_Face", (0.56, 0.02, 0.51), (0.16, -1.016, 2.66),
        emissive("#ffe5c0", 1.05), rot=(0, 0, math.radians(12)),
        collection=STORE)
    for side in (-1, 1):
        box(f"Blade_Neon_{side}", (0.022, 0.022, 0.55),
            (0.16 + side * 0.30, -1.022, 2.66), emissive("#ff73a8", 2.2),
            rot=(0, 0, math.radians(12)), collection=STORE)
    text_mesh("Blade_24H", "24H", 0.19, (0.16, -1.032, 2.75),
              matte("#7d3157"), rot=(math.pi / 2, 0, math.radians(12)),
              extrude=0.005, collection=STORE, bold=True)
    text_mesh("Blade_OPEN", "OPEN", 0.065, (0.16, -1.034, 2.61),
              emissive("#ef8d4f", 2.0), rot=(math.pi / 2, 0, math.radians(12)),
              extrude=0.002, collection=STORE)
    # Canopy: a deep eaves over the storefront with warm downlight strips.
    box("Canopy_Front", (3.28, 0.34, 0.065), (1.14, STORE_Y0 - 0.17, CANOPY_Z),
        matte("#d8d1be"), bevel=0.020, collection=STORE, outline=True)
    box("Canopy_Left", (0.34, 2.64, 0.065), (STORE_X0 - 0.17, 0.55, CANOPY_Z),
        matte("#d8d1be"), bevel=0.020, collection=STORE, outline=True)
    box("Canopy_Corner", (0.58, 0.58, 0.065), (STORE_X0 + 0.03, STORE_Y0 + 0.03, CANOPY_Z),
        matte("#d8d1be"), rot=(0, 0, -math.pi / 4), bevel=0.018,
        collection=STORE, outline=True)
    # A darker roof skin lets the eave recede while the warm underside stays inviting.
    box("Canopy_Top_Front", (3.12, 0.26, 0.012), (1.14, STORE_Y0 - 0.17, CANOPY_Z + 0.041),
        matte("#345a54"), collection=STORE)
    box("Canopy_Top_Left", (0.26, 2.48, 0.012), (STORE_X0 - 0.17, 0.55, CANOPY_Z + 0.041),
        matte("#345a54"), collection=STORE)
    for i in range(4):
        box(f"Canopy_Light_{i}", (0.33, 0.035, 0.014),
            (0.22 + i * 0.48, STORE_Y0 - 0.275, CANOPY_Z - 0.041),
            emissive("#ffd79a", 1.9), collection=STORE)
    for i in range(3):
        box(f"Canopy_Light_Left_{i}", (0.035, 0.30, 0.014),
            (STORE_X0 - 0.275, 0.10 + i * 0.44, CANOPY_Z - 0.041),
            emissive("#ffd79a", 1.9), collection=STORE)
    # Small lip and rain gutter along the canopy.
    box("Canopy_Gutter_Front", (3.32, 0.040, 0.036), (1.14, STORE_Y0 - 0.33, CANOPY_Z + 0.010),
        MAT["darksteel"], bevel=0.007, collection=STORE, outline=True)
    box("Canopy_Gutter_Left", (0.040, 2.68, 0.036), (STORE_X0 - 0.33, 0.55, CANOPY_Z + 0.010),
        MAT["darksteel"], bevel=0.007, collection=STORE, outline=True)
    # Warm light coves and a restrained mint neon edge make the eaves read at night.
    box("Canopy_Cove_Front", (3.10, 0.028, 0.014), (1.14, STORE_Y0 - 0.25, CANOPY_Z - 0.038),
        emissive("#ffc77f", 1.8), collection=STORE)
    box("Canopy_Cove_Left", (0.028, 2.48, 0.014), (STORE_X0 - 0.25, 0.55, CANOPY_Z - 0.038),
        emissive("#ffc77f", 1.8), collection=STORE)
    box("Canopy_Neon_Front", (3.30, 0.015, 0.017), (1.14, STORE_Y0 - 0.335, CANOPY_Z + 0.022),
        emissive("#7be4c8", 1.55), collection=STORE)
    box("Canopy_Neon_Left", (0.015, 2.64, 0.017), (STORE_X0 - 0.335, 0.55, CANOPY_Z + 0.022),
        emissive("#7be4c8", 1.55), collection=STORE)
    box("Fascia_Neon_Front", (2.24, 0.018, 0.020), (1.51, STORE_Y0 - 0.18, 2.47),
        emissive("#89f1d4", 1.2), collection=STORE)
    # Entrance diagonal and automatic doors.
    build_auto_door()
    # Doormat.
    box("Doormat", (0.92, 0.46, 0.025), (-0.16, -1.10, WALK_Z + 0.032),
        matte("#38484b"), rot=(0, 0, -math.pi / 4), bevel=0.012,
        collection=PROPS, outline=True)
    text_mesh("Doormat_Text", "WELCOME", 0.075, (-0.16, -1.115, WALK_Z + 0.049),
              matte("#cdbd9c"), rot=(0, 0, -math.pi / 4), extrude=0.001,
              collection=PROPS)
    # Window posters, kept just in front of the glass so they read from outside.
    poster_specs = [
        ("WPoster_1", 0.55, -0.48, 0.27, 0.34, "#f3d28b", "おでん", "全品 70円"),
        ("WPoster_3", 2.32, -0.52, 0.25, 0.32, "#87c8c2", "HOT", "COFFEE"),
        ("WPoster_Left", 0.16, -0.62, 0.26, 0.32, "#ecb95c", "からあげ", "揚げたて"),
    ]
    for name, x, z, w, h, col, line1, line2 in poster_specs:
        if name == "WPoster_Left":
            # The left poster is placed on the left facade, rotated 90 degrees.
            plane(name + "_Card", (w, h), (STORE_X0 - 0.024, 0.28, z + 1.25),
                  matte(col), rot=(math.pi / 2, 0, -math.pi / 2),
                  collection=STORE)
            text_mesh(name + "_A", line1, 0.085,
                      (STORE_X0 - 0.028, 0.28, z + 1.28),
                      matte("#ffffff"), rot=(math.pi / 2, 0, -math.pi / 2),
                      extrude=0.001, collection=STORE)
            text_mesh(name + "_B", line2, 0.060,
                      (STORE_X0 - 0.029, 0.28, z + 1.17),
                      matte("#6d3d26"), rot=(math.pi / 2, 0, -math.pi / 2),
                      extrude=0.001, collection=STORE)
        else:
            plane(name + "_Card", (w, h), (x, STORE_Y0 - 0.025, z + 1.35),
                  matte(col), rot=(math.pi / 2, 0, 0), collection=STORE)
            text_mesh(name + "_A", line1, 0.095,
                      (x, STORE_Y0 - 0.029, z + 1.40), matte("#ffffff"),
                      rot=(math.pi / 2, 0, 0), extrude=0.001, collection=STORE,
                      bold=True)
            text_mesh(name + "_B", line2, 0.062,
                      (x, STORE_Y0 - 0.030, z + 1.28), matte("#703d28"),
                      rot=(math.pi / 2, 0, 0), extrude=0.001, collection=STORE)
    # Notice board on the far right of the storefront.
    build_notice_board()
    # Awnings, posters and subtle rain drips on the glass.
    for i in range(8):
        x = 0.55 + i * 0.24
        drop = cylinder(f"GlassDrop_{i}", 0.012, RNG.uniform(0.07, 0.25),
                        (x, STORE_Y0 - 0.04, RNG.uniform(0.75, 2.1)),
                        decal("#c9f3ff", alpha=0.44, strength=0.8),
                        collection=FX, vertices=6)
        drop.scale[0] = 0.5
        drop.scale[1] = 0.5
    # Small warm lights under the canopy point down towards the pavement.
    for i in range(4):
        point_light(f"L_Canopy_{i}", (0.22 + i * 0.48, STORE_Y0 - 0.45, CANOPY_Z - 0.16),
                    8, (1.0, 0.60, 0.30), 0.3, LIGHTS)
    for i in range(3):
        point_light(f"L_Canopy_Left_{i}", (STORE_X0 - 0.46, 0.10 + i * 0.44, CANOPY_Z - 0.16),
                    7, (1.0, 0.60, 0.30), 0.28, LIGHTS)


def build_auto_door():
    # Track and threshold at the diagonal entrance.
    a = (STORE_X0, STORE_Y0 + CHAMFER)
    b = (STORE_X0 + CHAMFER, STORE_Y0)
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    box("Entrance_Threshold", (length + 0.08, 0.20, 0.035),
        (mid[0], mid[1], WALK_Z + 0.032), MAT["darksteel"],
        rot=(0, 0, angle), collection=STORE, outline=True)
    box("Entrance_Header", (length + 0.10, 0.12, 0.18),
        (mid[0], mid[1], GLASS_TOP - 0.04), MAT["teal"],
        rot=(0, 0, angle), collection=STORE, outline=True)
    # Sliding door roots: their local X axis follows the diagonal.
    for side, sign in (("L", -1), ("R", 1)):
        root = bpy.data.objects.new(f"DOOR_{side}", None)
        STORE.objects.link(root)
        root.empty_display_type = "PLAIN_AXES"
        root.location = (mid[0], mid[1], 0)
        root.rotation_euler = (0, 0, angle)
        root["vx_anim"] = f"door_{side.lower()}"
        root["vx_outline"] = False
        # Glass panel + its dark frame, placed in the root's local space.
        panel_x = sign * 0.23
        glass = box(f"DOOR_{side}_Glass", (0.44, 0.035, 1.94),
                    (0, 0, 0), MAT["glass_warm"], collection=STORE,
                    outline=True)
        # Re-parent while preserving the intended local transform.
        glass.parent = root
        glass.matrix_parent_inverse.identity()
        glass.location = (panel_x, 0, 1.27)
        glass.rotation_euler = (0, 0, 0)
        for piece, size, loc in (
            ("FrameTop", (0.48, 0.055, 0.055), (panel_x, 0, 2.23)),
            ("FrameBottom", (0.48, 0.055, 0.07), (panel_x, 0, 0.31)),
            ("FrameOuter", (0.055, 0.055, 1.98), (panel_x - 0.24, 0, 1.27)),
            ("FrameInner", (0.055, 0.055, 1.98), (panel_x + 0.24, 0, 1.27)),
        ):
            p = box(f"DOOR_{side}_{piece}", size, (0, 0, 0), MAT["teal"],
                    collection=STORE, outline=True)
            p.parent = root
            p.matrix_parent_inverse.identity()
            p.location = loc
        # Door handle.
        h = cylinder(f"DOOR_{side}_Handle", 0.015, 0.20, (0, 0, 0),
                     MAT["steel"], rot=(0, math.pi / 2, 0), collection=STORE,
                     vertices=8)
        h.parent = root
        h.matrix_parent_inverse.identity()
        h.location = (panel_x + sign * 0.14, -0.055, 1.02)
    # Sensor and its red LED.
    box("Door_Sensor", (0.42, 0.12, 0.075), (mid[0], mid[1] - 0.02, 2.34),
        MAT["darksteel"], rot=(0, 0, angle), bevel=0.012,
        collection=STORE, outline=True)
    cylinder("Door_Sensor_LED", 0.012, 0.012, (mid[0], mid[1] - 0.09, 2.34),
             emissive("#ff7b57", 4.0), rot=(math.pi / 2, 0, 0),
             collection=STORE, vertices=8)
    # Open sign hanging just inside the glass.
    box("Open_Sign", (0.34, 0.05, 0.14), (0.30, STORE_Y0 + 0.02, 1.90),
        emissive("#ffcf8a", 1.7), rot=(0, 0, angle), collection=STORE)
    text_mesh("Open_Sign_Text", "OPEN", 0.07, (0.30, STORE_Y0 - 0.012, 1.90),
              matte("#6e3c22"), rot=(math.pi / 2, 0, angle), extrude=0.001,
              collection=STORE)


def build_notice_board():
    # Freestanding community notice board near the alley mouth, kept out of the
    # shop window so the interior can breathe.
    x, y, z = 3.02, -1.12, WALK_Z + 0.02
    angle = math.radians(-24)
    for i, dx in enumerate((-0.25, 0.25)):
        box(f"Notice_Post_{i}", (0.05, 0.05, 0.94), (x + dx, y + 0.02, z + 0.47),
            MAT["darksteel"], rot=(0, 0, angle), bevel=0.006,
            collection=PROPS, outline=True)
    box("Notice_Frame", (0.62, 0.055, 0.62), (x, y, z + 1.18), MAT["wood"],
        rot=(0, 0, angle), bevel=0.015, collection=PROPS, outline=True)
    box("Notice_Cork", (0.54, 0.025, 0.54), (x, y - 0.033, z + 1.18),
        matte("#b08b5c"), rot=(0, 0, angle), bevel=0.006,
        collection=PROPS)
    colors = ["#e4d8a8", "#cf7e68", "#dfe9df", "#e8c879"]
    for i, col in enumerate(colors):
        px = x - 0.15 + (i % 2) * 0.16
        pz = z + 1.30 - (i // 2) * 0.18
        box(f"Notice_Poster_{i}", (0.12, 0.012, 0.15), (px, y - 0.050, pz),
            matte(col), rot=(0, 0, angle + RNG.uniform(-0.06, 0.06)),
            collection=PROPS)
    text_mesh("Notice_Title", "地域のお知らせ", 0.043, (x, y - 0.066, z + 1.43),
              matte("#493725"), rot=(math.pi / 2, 0, angle), extrude=0.001,
              collection=PROPS)
    box("Notice_Lamp", (0.48, 0.05, 0.025), (x, y - 0.055, z + 1.52),
        emissive("#ffe0a3", 1.6), rot=(0, 0, angle), collection=PROPS)
    point_light("L_Notice", (x, y - 0.20, z + 1.45), 7,
                (1.0, 0.73, 0.45), 0.2, LIGHTS)
    # Small upward-facing banner above the door.
    box("Entrance_Banner", (0.90, 0.05, 0.20), (-0.01, STORE_Y0 - 0.16, 2.30),
        matte("#f5e9cc"), rot=(0, 0, -math.pi / 4), bevel=0.012,
        collection=STORE, outline=True)
    text_mesh("Entrance_Banner_Text", "いらっしゃいませ", 0.066,
              (-0.01, STORE_Y0 - 0.188, 2.30), matte("#8a5337"),
              rot=(math.pi / 2, 0, -math.pi / 4), extrude=0.001,
              collection=STORE)


# ---------------------------------------------------------------------------
# Interior
# ---------------------------------------------------------------------------
def build_interior():
    # Warm ceiling panels and visible white ceiling.
    for row in range(2):
        for col in range(2):
            box(f"Ceiling_Light_{row}_{col}", (0.82, 0.25, 0.045),
                (0.38 + col * 1.20, 0.04 + row * 1.15, CEILING_Z - 0.035),
                emissive("#ffe8c1", 2.0), collection=INTERIOR)
    # Interior floor tile grid.
    for i in range(7):
        x = -0.22 + i * 0.48
        box(f"TileLine_X_{i}", (0.012, 2.4, 0.008), (x, 0.55, 0.205),
            matte("#9b998f"), collection=INTERIOR)
    for i in range(6):
        y = -0.55 + i * 0.45
        box(f"TileLine_Y_{i}", (2.8, 0.012, 0.008), (1.15, y, 0.206),
            matte("#9b998f"), collection=INTERIOR)
    # Green floor guide line from the entrance into the aisles.
    box("FloorGuide_Line", (0.045, 1.45, 0.012), (0.46, 0.36, 0.214),
        matte("#4b9b86"), rot=(0, 0, -0.38), collection=INTERIOR)
    poly("FloorGuide_Arrow_1", [(0.52, -0.05), (0.68, 0.05), (0.52, 0.15)],
         0.218, matte("#4b9b86"), collection=INTERIOR)
    # Back drink fridge wall.
    build_fridge_wall()
    # Ice-cream chest freezer.
    box("IceFreezer_Body", (0.82, 0.62, 0.74), (1.92, 1.36, 0.56),
        matte("#dfe3dc"), bevel=0.035, collection=INTERIOR, outline=True)
    box("IceFreezer_Lid", (0.74, 0.50, 0.065), (1.92, 1.36, 0.97),
        MAT["glass"], bevel=0.018, collection=INTERIOR)
    box("IceFreezer_Glow", (0.66, 0.42, 0.02), (1.92, 1.36, 0.915),
        emissive("#d6eff1", 1.4), collection=INTERIOR)
    text_mesh("IceFreezer_Label", "アイス", 0.09, (1.92, 1.02, 0.84),
              matte("#3b6f76"), rot=(math.pi / 2, 0, 0), extrude=0.001,
              collection=INTERIOR)
    # Central gondola shelves.
    make_shelf_unit("Shelf_A", 0.0, 1.06, 0.54, 1.08, 1.42, 3)
    make_shelf_unit("Shelf_B", 0.97, 1.06, 0.54, 1.08, 1.42, 3)
    # Front low food island / magazines.
    make_low_case()
    # Checkout counter and equipment.
    build_checkout()
    # A strong in-store promotional banner adds a saturated colour band to the
    # otherwise bright interior, visible from the street.
    box("Int_PromoBanner", (2.02, 0.035, 0.22), (1.34, 0.16, 2.14),
        matte("#d86457"), collection=INTERIOR, outline=True)
    text_mesh("Int_PromoBanner_Text", "おにぎり・お弁当  できたて", 0.075,
              (1.34, 0.137, 2.14), matte("#fff4df"), rot=(math.pi / 2, 0, 0),
              extrude=0.001, collection=INTERIOR, bold=True)
    box("Int_PromoBanner_Trim", (2.02, 0.025, 0.025), (1.34, 0.155, 2.03),
        emissive("#ffc276", 1.3), collection=INTERIOR)
    # Hanging category light boxes.
    for i, (x, label, col) in enumerate((
        (0.26, "おにぎり・お弁当", "#f2d18f"),
        (1.15, "お菓子・日用品", "#a9d6ca"),
    )):
        box(f"Hanging_Sign_{i}", (0.92, 0.08, 0.25), (x, 0.72, 2.24),
            matte("#f6f0df"), bevel=0.01, collection=INTERIOR)
        text_mesh(f"Hanging_Sign_Text_{i}", label, 0.065,
                  (x, 0.665, 2.24), matte("#3b4e49"), rot=(math.pi / 2, 0, 0),
                  extrude=0.001, collection=INTERIOR)
        box(f"Hanging_Sign_Light_{i}", (0.86, 0.05, 0.03),
            (x, 0.72, 2.12), emissive(col, 1.4), collection=INTERIOR)
    # Staff door / back room door on the back wall.
    box("StaffDoor", (0.48, 0.06, 1.92), (2.31, STORE_Y1 - 0.10, 1.15),
        matte("#8d9a94"), bevel=0.014, collection=INTERIOR, outline=True)
    box("StaffDoor_Window", (0.25, 0.025, 0.35), (2.31, STORE_Y1 - 0.14, 1.72),
        MAT["glass_warm"], collection=INTERIOR)
    text_mesh("StaffDoor_Sign", "STAFF ONLY", 0.048, (2.31, STORE_Y1 - 0.145, 1.36),
              matte("#f4efe0"), rot=(math.pi / 2, 0, 0), extrude=0.001,
              collection=INTERIOR)
    # Lockers and backroom clutter on the right side.
    for i in range(3):
        box(f"Locker_{i}", (0.28, 0.28, 0.85), (2.54, 0.40 + i * 0.33, 0.64),
            matte("#a4afa8"), bevel=0.018, collection=INTERIOR, outline=True)
        box(f"Locker_Handle_{i}", (0.04, 0.025, 0.09), (2.54, 0.27 + i * 0.33, 0.72),
            MAT["steel"], collection=INTERIOR)
    for i in range(2):
        box(f"StorageCrate_{i}", (0.42, 0.30, 0.18),
            (0.12 + i * 0.45, 1.68, 0.32), matte("#c7a676"),
            bevel=0.012, collection=INTERIOR, outline=True)
    # Larger vivid wall posters above the fridge bank.
    for i, (x, z, col, label) in enumerate((
        (0.06, 2.10, "#f0c25d", "NEW"),
        (0.52, 2.10, "#d87b6a", "SALE"),
        (0.98, 2.10, "#75b9b2", "HOT"),
        (1.40, 2.10, "#e6c879", "24H"),
    )):
        plane(f"Int_Poster_{i}", (0.34, 0.40), (x, STORE_Y1 - 0.115, z),
              matte(col), rot=(math.pi / 2, 0, math.pi), collection=INTERIOR)
        text_mesh(f"Int_Poster_Text_{i}", label, 0.065,
                  (x, STORE_Y1 - 0.12, z + 0.03), matte("#ffffff"),
                  rot=(math.pi / 2, 0, math.pi), extrude=0.001,
                  collection=INTERIOR, bold=True)
    # A couple of ceiling spot lights help the display cases pop.
    area_light("L_Interior_A", (0.65, 0.15, 2.40), (0, 0, 0), 105,
               (1.0, 0.72, 0.44), (1.5, 0.85), LIGHTS)
    area_light("L_Interior_B", (1.75, 0.95, 2.40), (0, 0, 0), 90,
               (1.0, 0.75, 0.47), (1.3, 0.85), LIGHTS)
    point_light("L_Interior_Glow", (0.85, 0.65, 1.55), 15,
                (1.0, 0.66, 0.36), 1.2, LIGHTS)
    # A warm front fill just inside the glass keeps the shelves readable from outside.
    point_light("L_Front_Interior", (1.15, -0.35, 1.85), 20,
                (1.0, 0.74, 0.46), 0.8, LIGHTS)
    # Steam from the hot counter.
    for i, (x, y, z0, h) in enumerate((
        (2.18, 1.18, 1.15, 0.55), (2.30, 1.14, 1.12, 0.38),
        (2.40, 1.20, 1.12, 0.45),
    )):
        pts = [(x, y, z0), (x + 0.04, y - 0.04, z0 + h * 0.45),
               (x - 0.02, y - 0.08, z0 + h)]
        curve_tube(f"Steam_{i}", pts, 0.022,
                   decal("#fff4d9", alpha=0.12, strength=0.5), collection=FX)


def build_fridge_wall():
    x0, x1 = -0.18, 1.44
    y = STORE_Y1 - 0.30
    box("Fridge_Cabinet", (x1 - x0 + 0.14, 0.58, 2.20),
        ((x0 + x1) / 2, y + 0.12, 1.30), matte("#e9e5da"),
        bevel=0.025, collection=INTERIOR, outline=True)
    box("Fridge_Backlight", (x1 - x0, 0.03, 1.72),
        ((x0 + x1) / 2, y - 0.14, 1.34), emissive("#d6f5ff", 1.9),
        collection=INTERIOR)
    box("Fridge_WarmTop", (x1 - x0, 0.035, 0.08),
        ((x0 + x1) / 2, y - 0.15, 2.20), emissive("#ffd28d", 1.6),
        collection=INTERIOR)
    # Three glass doors with rows of bottles.
    door_w = (x1 - x0) / 3
    for d in range(3):
        cx = x0 + door_w * (d + 0.5)
        box(f"Fridge_DoorFrame_{d}", (door_w + 0.04, 0.045, 2.03),
            (cx, y - 0.235, 1.30), MAT["teal"], bevel=0.008,
            collection=INTERIOR, outline=True)
        plane(f"Fridge_Glass_{d}", (door_w - 0.05, 1.92),
              (cx, y - 0.275, 1.32), MAT["glass"],
              rot=(math.pi / 2, 0, 0), collection=INTERIOR)
        for row in range(3):
            z = 0.53 + row * 0.53
            box(f"Fridge_Shelf_{d}_{row}", (door_w - 0.08, 0.24, 0.025),
                (cx, y - 0.04, z), MAT["steel"], collection=INTERIOR)
            for b in range(5):
                bx = cx - door_w * 0.33 + b * door_w * 0.17
                col = ["#e8a25e", "#90d4ca", "#d76b63", "#7ba7d3",
                       "#e2d076"][(d * 5 + row * 2 + b) % 5]
                cylinder(f"Fridge_Bottle_{d}_{row}_{b}", 0.034, 0.23,
                         (bx, y - 0.12, z + 0.14), matte(col),
                         collection=INTERIOR, vertices=8)
                cylinder(f"Fridge_Cap_{d}_{row}_{b}", 0.02, 0.028,
                         (bx, y - 0.12, z + 0.27), matte("#f2f2ee"),
                         collection=INTERIOR, vertices=8)
                box(f"Fridge_Label_{d}_{row}_{b}", (0.052, 0.004, 0.075),
                    (bx, y - 0.158, z + 0.13), matte("#f1f0e5"),
                    collection=INTERIOR)
    # Door handles and fridge light strips.
    for d in range(3):
        cx = x0 + door_w * (d + 0.5)
        box(f"Fridge_Handle_{d}", (0.022, 0.035, 0.60),
            (cx + door_w * 0.34, y - 0.30, 1.30), MAT["steel"],
            collection=INTERIOR)
        box(f"Fridge_LightStrip_{d}", (door_w - 0.10, 0.02, 0.025),
            (cx, y - 0.305, 2.29), emissive("#fff1c9", 2.0), collection=INTERIOR)


def make_shelf_unit(name, x, y, w, d, h, levels):
    box(f"{name}_Base", (w, d, 0.14), (x, y, 0.27), MAT["darksteel"],
        bevel=0.01, collection=INTERIOR, outline=True)
    box(f"{name}_Back", (w, 0.035, h), (x, y + d / 2 - 0.015, h / 2 + 0.28),
        matte("#799589"), collection=INTERIOR)
    for side in (-1, 1):
        box(f"{name}_Side_{side}", (0.035, d, h), (x + side * (w / 2 - 0.015),
            y, h / 2 + 0.28), matte("#c7c1b2"), collection=INTERIOR, outline=True)
    for level in range(levels):
        z = 0.37 + level * ((h - 0.22) / max(1, levels - 1))
        box(f"{name}_Shelf_{level}", (w - 0.04, d - 0.04, 0.032), (x, y, z),
            matte("#cfc9ba"), collection=INTERIOR, outline=True)
        # Merchandise: a row of small coloured cartons and packets.
        for k in range(5):
            cx = x - w * 0.32 + k * w * 0.16
            col = ["#d76654", "#e3b454", "#7ac1ad", "#7c9dc2",
                   "#dc8fa7", "#d9d270"][(level * 5 + k) % 6]
            if level == 0:
                box(f"{name}_Pack_{level}_{k}", (w * 0.11, d * 0.32, 0.20),
                    (cx, y - d * 0.12, z + 0.11), matte(col),
                    bevel=0.006, collection=INTERIOR)
            else:
                cylinder(f"{name}_Pack_{level}_{k}", w * 0.052, 0.15,
                         (cx, y - d * 0.10, z + 0.09), matte(col),
                         collection=INTERIOR, vertices=8)
        # Price rail and a small warm strip that makes the stock read at night.
        box(f"{name}_PriceRail_{level}", (w - 0.08, 0.018, 0.032),
            (x, y - d / 2 + 0.02, z - 0.055), matte("#f1e6c5"),
            collection=INTERIOR)
        box(f"{name}_ShelfLight_{level}", (w - 0.10, 0.018, 0.014),
            (x, y - d / 2 + 0.055, z - 0.075), emissive("#ffd894", 1.25),
            collection=INTERIOR)
    # Small category tabs at the shelf ends.
    for i, col in enumerate(("#7ac0b0", "#e3b356", "#d47a6b")):
        box(f"{name}_Tab_{i}", (0.12, 0.02, 0.09),
            (x - w * 0.27 + i * 0.14, y - d / 2 - 0.01, h + 0.13),
            matte(col), collection=INTERIOR)


def make_low_case():
    # Magazines along the window and a low chilled case for onigiri / bento.
    box("MagazineRack", (0.93, 0.34, 0.78), (0.80, -0.26, 0.61),
        matte("#aca59a"), bevel=0.018, collection=INTERIOR, outline=True)
    for i in range(4):
        box(f"MagazineShelf_{i}", (0.86, 0.27, 0.025),
            (0.80, -0.26, 0.37 + i * 0.14), MAT["darksteel"], collection=INTERIOR)
        for j in range(5):
            col = ["#e4ce77", "#c96d63", "#81bdb1", "#7e9ec7",
                   "#d897b2"][(i + j) % 5]
            box(f"Magazine_{i}_{j}", (0.13, 0.025, 0.19),
                (0.47 + j * 0.16, -0.43, 0.48 + i * 0.14),
                matte(col), bevel=0.003, collection=INTERIOR)
    box("OnigiriCase", (0.72, 0.42, 0.88), (1.50, -0.26, 0.65),
        matte("#d7d6cb"), bevel=0.022, collection=INTERIOR, outline=True)
    box("OnigiriCase_Glass", (0.66, 0.38, 0.024), (1.50, -0.27, 1.10),
        MAT["glass"], collection=INTERIOR)
    box("OnigiriCase_Light", (0.61, 0.32, 0.018), (1.50, -0.27, 1.075),
        emissive("#fff0cc", 1.6), collection=INTERIOR)
    # Triangular onigiri and bento boxes.
    for i in range(4):
        for j in range(2):
            cx = 1.28 + i * 0.14
            cy = -0.38 + j * 0.16
            cylinder(f"Onigiri_{i}_{j}", 0.078, 0.08, (cx, cy, 0.99),
                     matte("#f6efde"), vertices=3, rot=(0, 0, math.radians(90)),
                     collection=INTERIOR)
            box(f"Onigiri_Nori_{i}_{j}", (0.055, 0.082, 0.026),
                (cx, cy, 0.96), matte("#234236"), collection=INTERIOR)
    for i in range(3):
        box(f"Bento_{i}", (0.16, 0.15, 0.07), (1.29 + i * 0.17, -0.10, 0.98),
            matte("#d9c699"), bevel=0.008, collection=INTERIOR)
        box(f"Bento_Label_{i}", (0.12, 0.018, 0.024),
            (1.29 + i * 0.17, -0.184, 0.99), matte("#c35e55"),
            collection=INTERIOR)
    # Bento / deli menu above the case.
    box("Deli_Menu", (0.84, 0.035, 0.28), (1.52, -0.53, 1.44),
        matte("#f2e7ca"), collection=INTERIOR, outline=True)
    text_mesh("Deli_Menu_Text", "おにぎり・お弁当", 0.07,
              (1.52, -0.552, 1.47), matte("#8d4e39"),
              rot=(math.pi / 2, 0, 0), extrude=0.001, collection=INTERIOR)
    for i, txt in enumerate(("鮭", "明太子", "ツナ")):
        text_mesh(f"Deli_Label_{i}", txt, 0.035,
                  (1.22 + i * 0.18, -0.44, 1.16), matte("#3c564d"),
                  rot=(math.pi / 2, 0, 0), extrude=0.001, collection=INTERIOR)


def build_checkout():
    # Counter, register, card terminal, small display, and back counter.
    box("Checkout_Counter", (0.82, 0.52, 0.92), (2.17, 0.18, 0.66),
        matte("#d8d2c1"), bevel=0.028, collection=INTERIOR, outline=True)
    box("Checkout_Top", (0.90, 0.58, 0.06), (2.17, 0.18, 1.14),
        matte("#efe8d7"), bevel=0.012, collection=INTERIOR)
    box("POS_Base", (0.24, 0.15, 0.20), (2.16, 0.07, 1.26),
        MAT["darksteel"], bevel=0.012, collection=INTERIOR, outline=True)
    box("POS_Screen", (0.38, 0.035, 0.25), (2.16, -0.015, 1.47),
        emissive("#95e1dc", 1.4), rot=(0.22, 0, 0), bevel=0.008,
        collection=INTERIOR, outline=True)
    box("POS_ScreenDark", (0.33, 0.008, 0.20), (2.16, -0.038, 1.47),
        matte("#25595f"), rot=(0.22, 0, 0), collection=INTERIOR)
    box("Scanner", (0.22, 0.14, 0.09), (2.43, 0.24, 1.23),
        MAT["darksteel"], bevel=0.008, collection=INTERIOR)
    box("CardTerminal", (0.16, 0.12, 0.06), (1.92, 0.31, 1.19),
        matte("#d9dee0"), bevel=0.01, collection=INTERIOR)
    box("ReceiptPrinter", (0.22, 0.18, 0.18), (2.42, 0.06, 1.25),
        matte("#d9dcda"), bevel=0.01, collection=INTERIOR)
    # Acrylic sneeze guard, clear enough to keep the view open.
    plane("SneezeGuard", (0.72, 0.42), (2.07, 0.01, 1.34),
          glass("SNEEZE_GUARD", "#d6f3f4", 0.09), rot=(math.pi / 2, 0, 0), collection=INTERIOR)
    # Back counter with coffee machine, hot snack warmer and oden pot.
    box("BackCounter", (1.55, 0.45, 0.88), (1.55, 1.40, 0.63),
        matte("#c9c5b8"), bevel=0.022, collection=INTERIOR, outline=True)
    box("CoffeeMachine", (0.34, 0.30, 0.64), (2.33, 1.19, 1.24),
        MAT["darksteel"], bevel=0.016, collection=INTERIOR, outline=True)
    box("CoffeeScreen", (0.18, 0.015, 0.13), (2.33, 1.033, 1.44),
        emissive("#8ce0db", 1.5), collection=INTERIOR)
    cylinder("CoffeeCarafe", 0.07, 0.20, (2.42, 1.09, 1.05),
             MAT["glass"], collection=INTERIOR, vertices=12)
    box("CoffeeDripTray", (0.30, 0.16, 0.035), (2.33, 1.03, 0.93),
        MAT["steel"], collection=INTERIOR)
    box("HotSnackWarmer", (0.52, 0.40, 0.28), (1.72, 1.30, 1.13),
        MAT["darksteel"], bevel=0.012, collection=INTERIOR, outline=True)
    box("HotSnack_Glass", (0.44, 0.32, 0.22), (1.72, 1.28, 1.15),
        glass("HOTSNACK_GLASS", "#ffe4b4", 0.13), collection=INTERIOR)
    for i in range(4):
        box(f"HotSnack_{i}", (0.10, 0.08, 0.06),
            (1.57 + i * 0.10, 1.25, 1.04), matte("#b86c3e"),
            bevel=0.01, collection=INTERIOR)
    # Oden pot with compartments.
    box("Oden_Base", (0.48, 0.34, 0.15), (1.08, 1.30, 1.10),
        MAT["steel"], bevel=0.01, collection=INTERIOR, outline=True)
    for i in range(2):
        for j in range(2):
            box(f"Oden_Compartment_{i}_{j}", (0.20, 0.13, 0.018),
                (0.95 + i * 0.23, 1.22 + j * 0.15, 1.18),
                matte("#d6b77c"), bevel=0.005, collection=INTERIOR)
    text_mesh("Oden_Label", "おでん", 0.075, (1.08, 1.09, 1.25),
              emissive("#ffcf84", 1.2), rot=(math.pi / 2, 0, 0),
              extrude=0.002, collection=INTERIOR)
    # Bag rack and a small trash bin behind the counter.
    for i in range(4):
        box(f"BagRack_{i}", (0.25, 0.03, 0.18), (1.82 + i * 0.18, 0.08, 1.01),
            matte("#eee9d7"), collection=INTERIOR)
    cylinder("CounterBin", 0.13, 0.34, (2.44, 0.66, 0.42),
             matte("#737f7c"), collection=INTERIOR, vertices=12)
    # A wall menu and ATM lightbox add warm and cool pools of colour inside.
    box("Int_Wall_Menu", (0.04, 0.74, 0.46), (2.56, 1.16, 1.72),
        matte("#2a4b4c"), collection=INTERIOR, outline=True)
    box("Int_Wall_Menu_Face", (0.018, 0.66, 0.39), (2.53, 1.16, 1.72),
        emissive("#ffd89c", 1.4), collection=INTERIOR)
    text_mesh("Int_Wall_Menu_EN", "HOT FOOD  ·  COFFEE", 0.048,
              (2.51, 1.16, 1.79), matte("#6d3d28"),
              rot=(math.pi / 2, 0, -math.pi / 2), extrude=0.001,
              collection=INTERIOR)
    text_mesh("Int_Wall_Menu_JP", "できたて  お弁当", 0.058,
              (2.51, 1.16, 1.67), matte("#86512f"),
              rot=(math.pi / 2, 0, -math.pi / 2), extrude=0.001,
              collection=INTERIOR)
    box("Int_ATM_Panel", (0.05, 0.52, 0.42), (2.56, -0.34, 1.68),
        matte("#1f4857"), collection=INTERIOR, outline=True)
    box("Int_ATM_Face", (0.015, 0.45, 0.35), (2.525, -0.34, 1.68),
        emissive("#66e3df", 1.5), collection=INTERIOR)
    text_mesh("Int_ATM_Text", "ATM", 0.13, (2.505, -0.34, 1.70),
              matte("#174b57"), rot=(math.pi / 2, 0, -math.pi / 2),
              extrude=0.001, collection=INTERIOR, bold=True)
    # Pink neon inside the window creates a strong colour mirror in the rain below.
    box("Int_PinkNeon", (0.026, 0.032, 0.90), (0.72, -0.50, 1.78),
        emissive("#ff5b96", 2.6), collection=INTERIOR)
    box("Int_PinkNeon2", (0.026, 0.48, 0.032), (0.72, -0.27, 2.23),
        emissive("#ff5b96", 2.3), collection=INTERIOR)
    # Staff-only door light and a small warm point.
    point_light("L_Checkout", (2.15, 0.16, 1.90), 28,
                (1.0, 0.68, 0.40), 0.7, LIGHTS)
    text_mesh("Checkout_Sign", "レジ", 0.10, (2.17, -0.06, 1.73),
              matte("#f6edd4"), rot=(math.pi / 2, 0, 0), extrude=0.002,
              collection=INTERIOR)


def make_aircon(name, loc, rotz, scale=1.0, collection=None):
    x, y, z = loc
    box(f"{name}_Body", (0.72 * scale, 0.34 * scale, 0.50 * scale),
        (x, y, z), matte("#d4d3c8"), rot=(0, 0, rotz), bevel=0.03,
        collection=collection or STORE, outline=True)
    # Fan grille housed on the front face.
    cylinder(f"{name}_Fan", 0.16 * scale, 0.03, (x + 0.00, y - 0.18 * scale, z),
             matte("#4a5559"), rot=(math.pi / 2, 0, rotz), vertices=24,
             collection=collection or STORE)
    for i in range(4):
        box(f"{name}_Slat_{i}", (0.34 * scale, 0.02, 0.014),
            (x, y - 0.195 * scale, z - 0.10 * scale + i * 0.065 * scale),
            matte("#8f9794"), rot=(0, 0, rotz), collection=collection or STORE)
    for i in range(2):
        box(f"{name}_Foot_{i}", (0.12 * scale, 0.16 * scale, 0.07),
            (x - 0.22 * scale + i * 0.44 * scale, y + 0.03, z - 0.28 * scale),
            matte("#5c6260"), rot=(0, 0, rotz), collection=collection or STORE)
    # A little drip stain / pipe.
    box(f"{name}_Pipe", (0.045, 0.045, 0.30), (x + 0.30 * scale, y + 0.12, z - 0.19),
        MAT["steel"], collection=collection or STORE)


# ---------------------------------------------------------------------------
# Street props
# ---------------------------------------------------------------------------
def build_street_props():
    build_vending_machines()
    build_bicycle()
    build_umbrella_stand()
    build_bins()
    build_pavement_details()
    build_utility_pole()
    build_street_lamp()
    build_guardrail()
    build_road_signs()
    build_traffic_signal()
    build_bollards()
    # Entrance mat, bin and a small stack of crates.
    box("Crate_A", (0.36, 0.28, 0.20), (-1.94, 0.58, WALK_Z + 0.10),
        matte("#b38c5a"), bevel=0.012, collection=PROPS, outline=True)
    box("Crate_B", (0.34, 0.26, 0.18), (-1.94, 0.58, WALK_Z + 0.29),
        matte("#c39a64"), bevel=0.012, collection=PROPS, outline=True)
    # Toadstool-like rain pipe beside the store.
    cylinder("Downpipe", 0.045, 2.35, (2.75, -0.68, 1.30),
             MAT["steel"], collection=STORE, vertices=10)
    for i in range(5):
        cylinder(f"Downpipe_Joint_{i}", 0.055, 0.035,
                 (2.75, -0.68, 0.32 + i * 0.42), MAT["darksteel"],
                 collection=STORE, vertices=10)


def build_vending_machines():
    specs = [
        ("Vending_Cyan", -1.78, "#cfe7e8", "#5db6bf", "#e4f3ef"),
        ("Vending_Red", -1.18, "#c95b57", "#e6b55e", "#f2e1c2"),
    ]
    for idx, (name, x, body_col, accent, light_col) in enumerate(specs):
        y = -1.42
        z0 = WALK_Z + 0.02
        box(f"{name}_Body", (0.60, 0.60, 1.82), (x, y, z0 + 0.91),
            matte(body_col), bevel=0.035, collection=PROPS, outline=True)
        box(f"{name}_Front", (0.54, 0.035, 1.47), (x, y - 0.305, z0 + 0.94),
            matte("#eef1e4"), collection=PROPS)
        box(f"{name}_Display", (0.47, 0.025, 0.88), (x, y - 0.333, z0 + 1.15),
            emissive(light_col, 1.4), collection=PROPS)
        for row in range(3):
            box(f"{name}_ShelfGlow_{row}", (0.45, 0.026, 0.025),
                (x, y - 0.348, z0 + 0.82 + row * 0.24),
                emissive("#ffffff", 1.3), collection=PROPS)
            for col in range(4):
                c = ["#dd7056", "#78b8a5", "#e5c66e", "#7e9fce",
                     "#d78da5"][(row + col + idx) % 5]
                box(f"{name}_Can_{row}_{col}", (0.075, 0.035, 0.15),
                    (x - 0.165 + col * 0.105, y - 0.36, z0 + 0.90 + row * 0.24),
                    matte(c), bevel=0.012, collection=PROPS)
        # Buttons / coin slot / delivery flap.
        box(f"{name}_Panel", (0.46, 0.025, 0.18), (x, y - 0.352, z0 + 0.64),
            MAT["darksteel"], collection=PROPS)
        for b in range(3):
            cylinder(f"{name}_Button_{b}", 0.022, 0.013,
                     (x - 0.14 + b * 0.14, y - 0.369, z0 + 0.65),
                     matte(["#dfd9b5", "#b5d4c9", "#d9a27b"][b]),
                     rot=(math.pi / 2, 0, 0), collection=PROPS, vertices=10)
        box(f"{name}_Coin", (0.10, 0.022, 0.035), (x + 0.14, y - 0.375, z0 + 0.78),
            MAT["steel"], collection=PROPS)
        box(f"{name}_Flap", (0.34, 0.03, 0.20), (x, y - 0.36, z0 + 0.31),
            MAT["darksteel"], bevel=0.012, collection=PROPS, outline=True)
        box(f"{name}_TopSign", (0.53, 0.05, 0.20), (x, y - 0.30, z0 + 1.86),
            emissive(accent, 1.5), collection=PROPS)
        text_mesh(f"{name}_TopText", "DRINKS", 0.073, (x, y - 0.333, z0 + 1.87),
                  matte("#ffffff"), rot=(math.pi / 2, 0, 0), extrude=0.001,
                  collection=PROPS)
        # Light spill onto wet ground.
        point_light(f"L_Vending_{idx}", (x, y - 0.52, z0 + 0.80),
                    12, (0.48, 0.91, 0.94) if idx == 0 else (1.0, 0.62, 0.46),
                    0.3, LIGHTS)
        # Small recycle bin for cans.
        if idx == 1:
            cylinder("CanBin", 0.18, 0.46, (x + 0.48, y + 0.08, z0 + 0.23),
                     matte("#71847e"), collection=PROPS, vertices=16,
                     outline=True)
            cylinder("CanBin_Hole", 0.075, 0.015, (x + 0.48, y + 0.08, z0 + 0.47),
                     MAT["ink"], collection=PROPS, vertices=16)


def build_bicycle():
    root = bpy.data.objects.new("BicycleRoot", None)
    PROPS.objects.link(root)
    root.location = (3.02, -0.78, WALK_Z + 0.02)
    root.rotation_euler = (0, math.radians(-7), math.radians(84))
    parts = []

    def bpart(obj):
        obj.parent = root
        obj.matrix_parent_inverse.identity()
        # Existing world transforms are kept; group only for organization.
        parts.append(obj)
        return obj

    # Wheels, rims and spokes in the local XZ plane (normal along Y).
    for w, wx in (("Rear", -0.52), ("Front", 0.54)):
        torus(f"Bike_{w}_Tire", 0.335, 0.026, (0, 0, 0), matte("#1b1d20"),
              rot=(math.pi / 2, 0, 0), collection=PROPS, outline=True)
        o = bpy.context.object
        o.parent = root
        o.matrix_parent_inverse.identity()
        o.location = (wx, 0, 0.38)
        torus(f"Bike_{w}_Rim", 0.30, 0.012, (0, 0, 0), MAT["steel"],
              rot=(math.pi / 2, 0, 0), collection=PROPS)
        o = bpy.context.object
        o.parent = root
        o.matrix_parent_inverse.identity()
        o.location = (wx, 0, 0.38)
        cylinder(f"Bike_{w}_Hub", 0.032, 0.12, (0, 0, 0), MAT["steel"],
                 rot=(math.pi / 2, 0, 0), collection=PROPS,
                 vertices=10)
        o = bpy.context.object
        o.parent = root
        o.matrix_parent_inverse.identity()
        o.location = (wx, 0, 0.38)
        for s in range(10):
            a = 2 * math.pi * s / 10
            p1 = (wx, 0, 0.38)
            p2 = (wx + math.cos(a) * 0.30, 0, 0.38 + math.sin(a) * 0.30)
            spoke = curve_tube(f"Bike_{w}_Spoke_{s}", [p1, p2], 0.004,
                               MAT["steel"], collection=PROPS)
            spoke.parent = root
            spoke.matrix_parent_inverse.identity()
    # Frame tubes.
    def tube(name, pts, r=0.018, col=None):
        ob = curve_tube(name, pts, r, col or matte("#78a99c"),
                        collection=PROPS, outline=True)
        ob.parent = root
        ob.matrix_parent_inverse.identity()
        return ob
    tube("Bike_Frame_Top", [(-0.48, 0, 0.72), (0.02, 0, 0.92), (0.42, 0, 0.73)], 0.023)
    tube("Bike_Frame_Down", [(-0.38, 0, 0.43), (0.02, 0, 0.74), (0.42, 0, 0.43)], 0.020)
    tube("Bike_SeatTube", [(-0.36, 0, 0.45), (-0.43, 0, 0.88)], 0.019)
    tube("Bike_HeadTube", [(0.39, 0, 0.45), (0.47, 0, 0.94)], 0.021)
    tube("Bike_ChainStay", [(-0.52, 0, 0.38), (-0.32, 0, 0.45)], 0.018)
    tube("Bike_SeatStay", [(-0.52, 0, 0.38), (-0.42, 0, 0.84)], 0.015)
    tube("Bike_Fork", [(0.54, 0, 0.38), (0.47, 0, 0.92)], 0.015)
    tube("Bike_Handlebar", [(0.47, -0.22, 1.02), (0.47, 0, 0.98), (0.47, 0.22, 1.02)],
         0.015, MAT["steel"])
    tube("Bike_SeatPost", [(-0.43, 0, 0.84), (-0.45, 0, 1.03)], 0.015,
         MAT["steel"])
    box("Bike_Seat", (0.23, 0.11, 0.055), (0, 0, 0), matte("#2a2c2b"),
        bevel=0.03, collection=PROPS, outline=True)
    o = bpy.context.object
    o.parent = root
    o.matrix_parent_inverse.identity()
    o.location = (-0.46, 0, 1.05)
    # Basket at the front.
    for i in range(5):
        box(f"Bike_BasketBar_{i}", (0.025, 0.30, 0.025), (0, 0, 0),
            MAT["steel"], collection=PROPS)
        o = bpy.context.object
        o.parent = root
        o.matrix_parent_inverse.identity()
        o.location = (0.57 + i * 0.055, 0, 0.70 + (i % 2) * 0.06)
    box("Bike_BasketBase", (0.30, 0.30, 0.035), (0, 0, 0), MAT["steel"],
        collection=PROPS)
    o = bpy.context.object
    o.parent = root
    o.matrix_parent_inverse.identity()
    o.location = (0.69, 0, 0.67)
    # Folded clear umbrella in basket.
    cylinder("Bike_Umbrella", 0.045, 0.58, (0, 0, 0),
             glass("BIKE_UMBRELLA", "#d7f0f4", 0.44), rot=(0, 0.28, 0),
             collection=PROPS, vertices=12)
    o = bpy.context.object
    o.parent = root
    o.matrix_parent_inverse.identity()
    o.location = (0.72, 0, 0.92)
    # Pedals and kickstand.
    cylinder("Bike_Pedal", 0.035, 0.14, (0, 0, 0), MAT["darksteel"],
             rot=(math.pi / 2, 0, 0), collection=PROPS, vertices=8)
    o = bpy.context.object
    o.parent = root
    o.matrix_parent_inverse.identity()
    o.location = (0.02, 0, 0.30)
    tube("Bike_Kickstand", [(-0.52, 0, 0.38), (-0.61, 0.03, 0.02)], 0.012,
         MAT["steel"])
    # Small lamp on the handlebar.
    cylinder("Bike_Lamp", 0.055, 0.08, (0, 0, 0), emissive("#ffe8b0", 1.2),
             rot=(math.pi / 2, 0, 0), collection=PROPS, vertices=12)
    o = bpy.context.object
    o.parent = root
    o.matrix_parent_inverse.identity()
    o.location = (0.53, -0.19, 0.82)


def build_umbrella_stand():
    x, y, z = -0.76, -0.99, WALK_Z + 0.02
    cylinder("UmbrellaStand", 0.16, 0.56, (x, y, z + 0.28),
             MAT["darksteel"], collection=PROPS, vertices=16, outline=True)
    cylinder("UmbrellaStand_Inner", 0.13, 0.03, (x, y, z + 0.56),
             MAT["ink"], collection=PROPS, vertices=16)
    umbrellas = [
        (0.03, 0.00, "#c76d62", -0.16),
        (-0.04, 0.03, "#ebe4d0", 0.12),
        (0.02, -0.04, "#8fb8b2", 0.0),
    ]
    for i, (dx, dy, col, tilt) in enumerate(umbrellas):
        cyl = cylinder(f"Umbrella_{i}", 0.028, 0.74,
                       (x + dx, y + dy, z + 0.77), matte(col),
                       rot=(0.11, tilt, 0), collection=PROPS, vertices=10)
        curve_tube(f"Umbrella_Handle_{i}",
                   [(x + dx, y + dy, z + 1.10),
                    (x + dx + 0.08, y + dy + 0.01, z + 1.22),
                    (x + dx + 0.13, y + dy, z + 1.16)],
                   0.018, MAT["darksteel"], collection=PROPS)
    text_mesh("Umbrella_Label", "傘", 0.09, (x, y - 0.176, z + 0.35),
              matte("#f3ead2"), rot=(math.pi / 2, 0, 0), extrude=0.001,
              collection=PROPS)


def build_bins():
    specs = [
        ("Bin_Can", -1.94, -0.98, "#5fa7a4", "かん"),
        ("Bin_Bottle", -1.64, -0.98, "#c99758", "びん"),
        ("Bin_Paper", -1.34, -0.98, "#7f91a6", "紙"),
    ]
    for name, x, y, col, label in specs:
        box(f"{name}_Body", (0.28, 0.28, 0.58), (x, y, WALK_Z + 0.31),
            matte(col), bevel=0.02, collection=PROPS, outline=True)
        box(f"{name}_Lid", (0.29, 0.29, 0.045), (x, y, WALK_Z + 0.62),
            matte("#2d3d3d"), bevel=0.012, collection=PROPS)
        text_mesh(f"{name}_Label", label, 0.07, (x, y - 0.148, WALK_Z + 0.42),
                  matte("#ffffff"), rot=(math.pi / 2, 0, 0), extrude=0.001,
                  collection=PROPS)


def build_pavement_details():
    # Small potted shrubs by the frontage.
    for i, (px, py, scale) in enumerate(((2.46, -1.14, 1.0), (-0.48, -1.34, 0.85))):
        cylinder(f"Planter_{i}", 0.14 * scale, 0.28 * scale,
                 (px, py, WALK_Z + 0.14 * scale), matte("#a7674e"),
                 collection=PROPS, vertices=12, outline=True)
        for k, (dx, dy, s) in enumerate(((0.0, 0.0, 1.0), (0.10, -0.03, 0.7),
                                          (-0.09, 0.02, 0.65))):
            sphere(f"Planter_Leaf_{i}_{k}", 0.14 * scale * s,
                   (px + dx, py + dy, WALK_Z + 0.36 * scale + 0.08 * k),
                   matte("#497e5c"), collection=PROPS, outline=False,
                   segments=12, rings=8)
        # A tiny sign tucked in the pot.
        box(f"Planter_Sign_{i}", (0.18, 0.02, 0.12),
            (px, py - 0.125, WALK_Z + 0.25), matte("#f1dfb1"),
            rot=(0, 0, math.radians(-9)), collection=PROPS)


def build_utility_pole():
    x, y = -3.08, -0.45
    cylinder("UtilityPole", 0.115, 5.3, (x, y, 2.65), matte("#8b8d86"),
             collection=PROPS, vertices=14, outline=True)
    for i in range(4):
        cylinder(f"UtilityPole_Band_{i}", 0.125, 0.08, (x, y, 1.05 + i * 1.15),
                 matte("#555b5b"), collection=PROPS, vertices=14)
    box("UtilityPole_Stripe", (0.23, 0.23, 0.65), (x, y, 0.42),
        matte("#d0a04f"), collection=PROPS, outline=True)
    # Crossarms and insulators.
    for z in (4.25, 4.60):
        box(f"Utility_Crossarm_{z}", (1.15, 0.10, 0.08), (x, y, z),
            MAT["darksteel"], collection=PROPS, outline=True)
        for i in range(3):
            ix = x - 0.43 + i * 0.43
            cylinder(f"Utility_Insulator_{z}_{i}", 0.045, 0.18,
                     (ix, y, z + 0.14), matte("#d9e3dc"),
                     collection=PROPS, vertices=8)
            cylinder(f"Utility_InsulatorCap_{z}_{i}", 0.028, 0.05,
                     (ix, y, z + 0.25), MAT["steel"],
                     collection=PROPS, vertices=8)
    # Transformer and a junction box.
    cylinder("Transformer", 0.20, 0.56, (x + 0.25, y + 0.01, 3.70),
             matte("#6f7778"), collection=PROPS, vertices=16, outline=True)
    box("Utility_JunctionBox", (0.32, 0.20, 0.40), (x + 0.25, y - 0.02, 2.75),
        matte("#a1a49b"), bevel=0.015, collection=PROPS, outline=True)
    # Wires sweep over the street towards the back-right neighbourhood.
    anchors = [
        (-0.40, 0.05, 4.42), (0.55, 0.05, 4.50), (1.55, 0.05, 4.46),
        (-0.35, 0.12, 4.62), (0.70, 0.12, 4.74), (1.82, 0.12, 4.66),
    ]
    for i, (ax, ay, az) in enumerate(anchors):
        end = (3.25, 1.70 + i * 0.04, 3.65 + i * 0.12)
        p0 = (x - 0.38 + (i % 3) * 0.36, y, 4.33 + (i // 3) * 0.36)
        p1 = ((p0[0] + end[0]) / 2, (p0[1] + end[1]) / 2, min(p0[2], end[2]) - 0.55)
        p2 = end
        curve_tube(f"PowerLine_{i}", [p0, p1, p2], 0.007,
                   matte("#1a1b20"), collection=PROPS)
    # A street banner strapped to the pole.
    box("Pole_StreetBanner", (0.48, 0.035, 0.62), (x + 0.18, y - 0.14, 2.20),
        matte("#d7c89e"), rot=(0, 0, -0.08), bevel=0.01,
        collection=PROPS, outline=True)
    text_mesh("Pole_Banner_Text", "星見坂", 0.16, (x + 0.18, y - 0.166, 2.29),
              matte("#536962"), rot=(math.pi / 2, 0, -0.08), extrude=0.001,
              collection=PROPS, bold=True)
    text_mesh("Pole_Banner_Sub", "HOSHIMI-ZAKA", 0.045,
              (x + 0.18, y - 0.168, 2.10), matte("#8a6a4a"),
              rot=(math.pi / 2, 0, -0.08), extrude=0.001,
              collection=PROPS)


def build_street_lamp():
    x, y = -2.90, -1.55
    cylinder("StreetLamp_Pole", 0.055, 3.28, (x, y, 1.76),
             MAT["darksteel"], collection=PROPS, vertices=12, outline=True)
    curve_tube("StreetLamp_Arm", [(x, y, 3.20), (x + 0.24, y - 0.12, 3.46),
                                  (x + 0.68, y - 0.18, 3.36)],
               0.035, MAT["darksteel"], collection=PROPS, outline=True)
    box("StreetLamp_Head", (0.30, 0.22, 0.16), (x + 0.70, y - 0.18, 3.30),
        MAT["darksteel"], bevel=0.03, collection=PROPS, outline=True)
    box("StreetLamp_Glass", (0.24, 0.16, 0.055), (x + 0.70, y - 0.18, 3.22),
        emissive("#fff0c0", 3.0), bevel=0.02, collection=PROPS)
    point_light("L_StreetLamp", (x + 0.70, y - 0.18, 3.10), 85,
                (1.0, 0.72, 0.40), 0.45, LIGHTS, shadow=True)
    spot_light("L_StreetLamp_Cone", (x + 0.70, y - 0.18, 3.15),
               (0, 0, 0), 55, (1.0, 0.68, 0.34), math.radians(75), 0.55,
               LIGHTS, shadow=False)
    # Small base box.
    cylinder("StreetLamp_Base", 0.13, 0.12, (x, y, 0.20),
             matte("#4b5150"), collection=PROPS, vertices=12)


def build_guardrail():
    # Low white corner guardrail with separate posts and rounded rails.
    posts = [(-2.02, -1.55), (-2.02, -0.55), (-2.02, 0.45)]
    for i, (x, y) in enumerate(posts):
        cylinder(f"Guardrail_Post_{i}", 0.045, 0.78, (x, y, WALK_Z + 0.42),
                 matte("#d6d4c7"), collection=PROPS, vertices=8, outline=True)
        cylinder(f"Guardrail_Cap_{i}", 0.06, 0.05, (x, y, WALK_Z + 0.83),
                 matte("#b6b4a8"), collection=PROPS, vertices=8)
    # One short guardrail along the left road keeps the shop frontage uncluttered.
    for k in (-0.20, 0.20):
        curve_tube(f"Guardrail_Rail_{k}", [(-2.02 + k, -1.48, 0.76),
                                          (-2.02 + k, 0.40, 0.76)],
                   0.026, matte("#e5e1d1"), collection=PROPS, outline=True)


def build_road_signs():
    # Pedestrian crossing sign.
    x, y = -2.72, -2.12
    cylinder("RoadSign_Pole", 0.023, 2.18, (x, y, 1.16), MAT["steel"],
             collection=PROPS, vertices=10, outline=True)
    cylinder("RoadSign_BlueDisc", 0.21, 0.03, (x, y - 0.03, 2.24),
             matte("#3b7db2"), rot=(math.pi / 2, 0, 0), collection=PROPS,
             vertices=24, outline=True)
    # Stylised pedestrian figure and white base line.
    box("RoadSign_Crossing", (0.30, 0.015, 0.025), (x, y - 0.053, 2.17),
        matte("#eef2e8"), collection=PROPS)
    for i in range(3):
        box(f"RoadSign_Figure_{i}", (0.055, 0.014, 0.10 + i * 0.04),
            (x - 0.11 + i * 0.10, y - 0.055, 2.26 + (i % 2) * 0.04),
            matte("#f6f1dd"), collection=PROPS)
    # Parking sign near the bay.
    x2, y2 = 2.75, -2.02
    cylinder("ParkSign_Pole", 0.023, 2.15, (x2, y2, 1.16), MAT["steel"],
             collection=PROPS, vertices=10, outline=True)
    box("ParkSign_Board", (0.40, 0.035, 0.48), (x2, y2 - 0.025, 2.22),
        matte("#e7e3d6"), bevel=0.012, collection=PROPS, outline=True)
    text_mesh("ParkSign_P", "P", 0.31, (x2, y2 - 0.051, 2.28),
              matte("#4b766d"), rot=(math.pi / 2, 0, 0), extrude=0.001,
              collection=PROPS, bold=True)
    text_mesh("ParkSign_Text", "24H", 0.055, (x2, y2 - 0.052, 2.02),
              matte("#7a6b55"), rot=(math.pi / 2, 0, 0), extrude=0.001,
              collection=PROPS)
    # Small directional arrow sign on the utility pole area.
    box("DirSign", (0.68, 0.025, 0.18), (-2.78, -0.10, 1.85),
        matte("#547c78"), rot=(0, 0, -0.05), bevel=0.008,
        collection=PROPS, outline=True)
    text_mesh("DirSign_Text", "駅前 →", 0.085, (-2.78, -0.121, 1.85),
              matte("#f6f1de"), rot=(math.pi / 2, 0, -0.05), extrude=0.001,
              collection=PROPS)


def build_traffic_signal():
    # A small distant pedestrian signal at the far end of the left street.
    x, y = -2.72, 2.75
    cylinder("Traffic_Pole", 0.05, 3.20, (x, y, 1.60), MAT["steel"],
             collection=PROPS, vertices=12, outline=True)
    box("Traffic_Head", (0.28, 0.15, 0.62), (x, y, 2.94),
        MAT["darksteel"], bevel=0.025, collection=PROPS, outline=True)
    for i, (col, z, name) in enumerate((
        ("#e2584e", 3.12, "TRAFFIC_RED"),
        ("#e4b356", 2.94, "TRAFFIC_AMBER"),
        ("#62bdb0", 2.76, "TRAFFIC_GREEN"),
    )):
        mat = emissive(col, {"TRAFFIC_RED": 0.18, "TRAFFIC_AMBER": 0.15,
                             "TRAFFIC_GREEN": 2.8}[name])
        cylinder(name, 0.078, 0.035, (x, y - 0.09, z), mat,
                 rot=(math.pi / 2, 0, 0), collection=PROPS, vertices=16,
                 anim=name)
    # Small white pedestrian signal below.
    box("Traffic_PedBox", (0.22, 0.14, 0.34), (x, y, 2.35),
        MAT["darksteel"], bevel=0.015, collection=PROPS, outline=True)
    box("Traffic_PedRed", (0.09, 0.02, 0.09), (x, y - 0.08, 2.43),
        emissive("#e3685e", 1.0), collection=PROPS)
    box("Traffic_PedGreen", (0.09, 0.02, 0.09), (x, y - 0.08, 2.27),
        emissive("#78d0b2", 0.2), collection=PROPS)


def build_bollards():
    for i, (x, y) in enumerate(((-2.28, -0.90), (-2.28, 0.20), (2.88, 0.40))):
        cylinder(f"Bollard_{i}", 0.065, 0.62, (x, y, WALK_Z + 0.31),
                 matte("#6c7571"), collection=PROPS, vertices=10, outline=True)
        cylinder(f"Bollard_Band_{i}", 0.072, 0.06, (x, y, WALK_Z + 0.49),
                 emissive("#d6b15d", 0.35), collection=PROPS, vertices=10)


# ---------------------------------------------------------------------------
# Neighbours / alley / rooftop details
# ---------------------------------------------------------------------------
def build_neighbourhood():
    # A little apartment block behind the shop. Its rear face is fully dressed
    # below so orbiting behind the diorama never lands on a blank black wall.
    box("Neighbor_Block", (3.65, 1.40, 2.55), (1.65, 2.77, 1.40),
        matte("#4d514f"), bevel=0.04, collection=NEIGHBOR, outline=True)
    box("Neighbor_Parapet", (3.72, 1.48, 0.16), (1.65, 2.77, 2.75),
        matte("#606560"), bevel=0.02, collection=NEIGHBOR, outline=True)
    # Balconies and warm windows.
    for i in range(3):
        x = 0.55 + i * 0.95
        box(f"Neighbor_Window_{i}", (0.64, 0.06, 0.56), (x, 2.055, 1.85),
            matte("#5c6866"), bevel=0.014, collection=NEIGHBOR, outline=True)
        box(f"Neighbor_Window_Glow_{i}", (0.53, 0.03, 0.44), (x, 2.015, 1.85),
            emissive(["#ffd89b", "#ffd89b", "#7fbfd0"][i], 1.25),
            collection=NEIGHBOR)
        box(f"Neighbor_Balcony_{i}", (0.78, 0.38, 0.08), (x, 1.92, 1.44),
            matte("#6e746d"), bevel=0.012, collection=NEIGHBOR, outline=True)
        for k in range(4):
            box(f"Neighbor_BalconyBar_{i}_{k}", (0.025, 0.025, 0.43),
                (x - 0.30 + k * 0.20, 1.78, 1.66), matte("#8d938a"),
                collection=NEIGHBOR)
    # Roof rails, pipes and an air-con.
    box("Neighbor_RoofRail", (3.6, 0.04, 0.04), (1.65, 2.07, 2.72),
        matte("#a4a89f"), collection=NEIGHBOR)
    cylinder("Neighbor_Downpipe", 0.05, 2.5, (-0.10, 2.05, 1.28),
             MAT["steel"], collection=NEIGHBOR, vertices=10)
    make_aircon("AC_Neighbor", (-0.15, 2.05, 2.05), math.pi / 2, scale=0.9,
                 collection=NEIGHBOR)
    # Utility boxes / meter cabinet.
    box("MeterBox", (0.30, 0.18, 0.44), (2.95, 2.05, 1.18),
        matte("#9c9e92"), bevel=0.015, collection=NEIGHBOR, outline=True)
    # A small fictional snack-bar neon sign adds a magenta layer to the far corner.
    box("Neon_Snack_Back", (0.48, 0.08, 0.94), (3.18, 2.02, 2.08),
        matte("#2b1d2c"), bevel=0.015, collection=NEIGHBOR, outline=True)
    box("Neon_Snack_Face", (0.40, 0.022, 0.84), (3.18, 1.972, 2.08),
        emissive("#2a1b25", 1.0), collection=NEIGHBOR)
    for side in (-1, 1):
        box(f"Neon_Snack_Tube_{side}", (0.022, 0.022, 0.86),
            (3.18 + side * 0.20, 1.957, 2.08), emissive("#ff5f9d", 2.4),
            collection=NEIGHBOR)
    text_mesh("Neon_Snack_Text", "スナック", 0.115,
              (3.18, 1.945, 2.22), emissive("#ff9bc0", 2.0),
              rot=(math.pi / 2, 0, 0), extrude=0.002,
              collection=NEIGHBOR)
    text_mesh("Neon_Snack_Sub", "星", 0.15,
              (3.18, 1.945, 1.92), emissive("#ffd58a", 2.1),
              rot=(math.pi / 2, 0, 0), extrude=0.002,
              collection=NEIGHBOR, bold=True)
    point_light("L_Neon_Snack", (3.10, 1.80, 2.05), 15,
                (1.0, 0.26, 0.56), 0.5, LIGHTS)
    # Low back wall on the far-left edge.
    box("BackWall", (1.72, 0.22, 1.15), (-2.78, 3.40, 0.72),
        matte("#5c605c"), bevel=0.02, collection=NEIGHBOR, outline=True)
    text_mesh("BackWall_NoParking", "駐車禁止", 0.09, (-2.78, 3.275, 1.02),
              matte("#cfcabb"), rot=(math.pi / 2, 0, 0), extrude=0.001,
              collection=NEIGHBOR)
    # Build the narrow alley on the right side of the shop.
    box("Alley_Floor", (0.96, 2.55, 0.04), (3.03, 0.22, WALK_Z + 0.02),
        wet("ALLEY_WET", "#1a2227", 1.0, 0.12), collection=ALLEY)
    box("Alley_Fence", (0.10, 2.65, 1.24), (3.47, 0.25, WALK_Z + 0.60),
        matte("#6f6658"), bevel=0.016, collection=ALLEY, outline=True)
    for i in range(4):
        box(f"Alley_FenceRail_{i}", (0.04, 2.45, 0.045),
            (3.41, 0.25, WALK_Z + 0.24 + i * 0.27),
            matte("#8c8372"), collection=ALLEY)
    # Hanging noren and a warm lantern at the alley entrance.
    box("Alley_SignTop", (0.28, 0.10, 0.10), (3.22, -0.83, 2.02),
        MAT["darksteel"], collection=ALLEY, outline=True)
    box("Alley_Noren", (0.64, 0.035, 0.60), (3.12, -0.83, 1.67),
        matte("#6a4b44"), bevel=0.01, collection=ALLEY, outline=True)
    text_mesh("Alley_Noren_Text", "路地", 0.14, (3.12, -0.854, 1.72),
              matte("#e4d7b9"), rot=(math.pi / 2, 0, 0), extrude=0.001,
              collection=ALLEY)
    cylinder("Alley_Lantern", 0.12, 0.26, (3.26, -0.94, 1.93),
             emissive("#ffc779", 2.0), collection=ALLEY, vertices=16,
             outline=True)
    for i in range(2):
        cylinder(f"Alley_Lantern_Ring_{i}", 0.125, 0.022,
                 (3.26, -0.94, 1.82 + i * 0.22), MAT["ink"],
                 collection=ALLEY, vertices=16)
    point_light("L_Alley_Lantern", (3.26, -0.94, 1.82), 10,
                (1.0, 0.58, 0.30), 0.3, LIGHTS)
    # Air-con and crate details inside the alley.
    make_aircon("AC_Alley", (3.22, 1.42, 0.60), math.pi / 2, scale=0.8,
                 collection=ALLEY)
    for i in range(2):
        box(f"Alley_Crate_{i}", (0.38, 0.30, 0.20),
            (3.16, 0.05 + i * 0.36, WALK_Z + 0.11 + i * 0.02),
            matte("#9e7a4e"), bevel=0.01, collection=ALLEY, outline=True)
    box("Alley_Box", (0.30, 0.28, 0.22), (3.15, 1.03, WALK_Z + 0.12),
        matte("#b8a98a"), bevel=0.01, collection=ALLEY, outline=True)
    # Rain gutter / drip chain.
    for i in range(6):
        torus(f"Alley_Chain_{i}", 0.035, 0.009,
              (2.98, -0.46, 2.45 - i * 0.12), MAT["steel"],
              rot=(0, math.pi / 2, 0), collection=FX, major_seg=8,
              minor_seg=4)
    # Hanging shop curtain at the back of the alley, lit from within.
    box("Alley_BackDoor", (0.56, 0.05, 1.55), (3.18, 1.85, 0.95),
        matte("#4f5551"), bevel=0.014, collection=ALLEY, outline=True)
    box("Alley_BackDoor_Light", (0.16, 0.02, 0.18), (3.18, 1.812, 1.45),
        emissive("#ffd79e", 1.5), collection=ALLEY)
    # "No parking" mini sign near the alley entrance.
    box("Alley_Sign", (0.34, 0.03, 0.22), (2.92, -0.82, 2.38),
        matte("#d7d4c5"), bevel=0.01, collection=ALLEY, outline=True)
    text_mesh("Alley_Sign_Text", "路地入口", 0.060, (2.92, -0.838, 2.38),
              matte("#5e5f55"), rot=(math.pi / 2, 0, 0), extrude=0.001,
              collection=ALLEY)
    # A final low wall at the base rear, mostly hidden, helps close the silhouette.
    box("Rear_EdgeWall", (2.8, 0.12, 0.7), (-0.7, 3.42, 0.48),
        matte("#4f5654"), bevel=0.012, collection=NEIGHBOR, outline=True)


def rear_window(name, x, z, w, h, glow_col, cool=False):
    """A shallow, lit window on the neighbour's rear wall (facing +Y)."""
    frame_mat = matte("#34433f")
    box(f"{name}_Frame", (w + 0.10, 0.028, h + 0.10), (x, 3.492, z),
        frame_mat, bevel=0.008, collection=NEIGHBOR, outline=True)
    plane(f"{name}_Glow", (w, h), (x, 3.510, z), emissive(glow_col, 1.35),
          rot=(math.pi / 2, 0, math.pi), collection=NEIGHBOR)
    # Curtains, a mullion and a sill stop the pane looking like a plain card.
    for side in (-1, 1):
        box(f"{name}_Curtain_{side}", (w * 0.24, 0.012, h * 0.94),
            (x + side * w * 0.31, 3.520, z), matte("#e9d9bd" if side < 0 else "#9ab1a7"),
            collection=NEIGHBOR)
    box(f"{name}_Mullion", (0.018, 0.024, h), (x, 3.522, z),
        matte("#3b4945"), collection=NEIGHBOR)
    box(f"{name}_Sill", (w + 0.16, 0.075, 0.035), (x, 3.525, z - h / 2 - 0.065),
        matte("#6f7971"), bevel=0.006, collection=NEIGHBOR, outline=True)
    # A small silhouette on the sill gives the window some life.
    cylinder(f"{name}_Pot", 0.046, 0.09, (x + w * 0.28, 3.530, z - h / 2 - 0.005),
             matte("#a36c4e"), collection=NEIGHBOR, vertices=10)
    sphere(f"{name}_Plant", 0.075, (x + w * 0.28, 3.530, z - h / 2 + 0.075),
           matte("#4f7b5a"), collection=NEIGHBOR, segments=10, rings=6)
    # A little candy-striped awning.
    box(f"{name}_Awning", (w + 0.18, 0.12, 0.035), (x, 3.535, z + h / 2 + 0.10),
        matte("#dbc69d" if not cool else "#9ec4c0"), rot=(math.radians(-12), 0, 0),
        bevel=0.008, collection=NEIGHBOR, outline=True)
    for i in range(3):
        box(f"{name}_AwningStripe_{i}", (w * 0.16, 0.008, 0.034),
            (x - w * 0.28 + i * w * 0.28, 3.471, z + h / 2 + 0.10),
            matte("#c46b5c" if i % 2 == 0 else "#f2e3c9"),
            rot=(math.radians(-12), 0, 0), collection=NEIGHBOR)


def build_back_elevation():
    """Dress the rear facade, rooftop and service yard so the model reads from all sides."""
    # Facade layers / panel seams.
    box("Rear_BaseBand", (3.52, 0.030, 0.48), (1.65, 3.480, 0.40),
        matte("#574a42"), bevel=0.006, collection=NEIGHBOR, outline=True)
    box("Rear_Siding", (3.44, 0.018, 1.82), (1.65, 3.470, 1.56),
        matte("#69766e"), collection=NEIGHBOR)
    box("Rear_SidingTrim", (3.50, 0.022, 0.055), (1.65, 3.478, 2.55),
        matte("#353e3b"), collection=NEIGHBOR)
    for i in range(5):
        box(f"Rear_Seam_{i}", (0.012, 0.010, 1.72),
            (-0.08 + i * 0.82, 3.459, 1.54), matte("#56655e"),
            collection=NEIGHBOR)
    # Shallow eaves and a gutter.
    box("Rear_Eave", (3.54, 0.090, 0.055), (1.65, 3.535, 2.60),
        matte("#3e4642"), bevel=0.01, collection=NEIGHBOR, outline=True)
    box("Rear_Gutter", (3.56, 0.030, 0.030), (1.65, 3.590, 2.565),
        MAT["steel"], collection=NEIGHBOR)
    cylinder("Rear_Downpipe_L", 0.030, 2.32, (-0.06, 3.505, 1.36),
             MAT["steel"], collection=NEIGHBOR, vertices=10)
    cylinder("Rear_Downpipe_R", 0.028, 2.32, (3.33, 3.505, 1.36),
             MAT["steel"], collection=NEIGHBOR, vertices=10)
    # Lit windows.
    rear_window("RearWindow_A", 0.47, 1.97, 0.64, 0.50, "#ffcf92")
    rear_window("RearWindow_B", 1.38, 2.04, 0.48, 0.40, "#b8d9dc", cool=True)
    # A horizontal house name board.
    box("Rear_HouseSign", (0.94, 0.026, 0.22), (0.95, 3.495, 2.48),
        matte("#d7c39c"), bevel=0.008, collection=NEIGHBOR, outline=True)
    text_mesh("Rear_HouseSign_JP", "星見荘", 0.095, (0.95, 3.517, 2.50),
              matte("#46534c"), rot=(math.pi / 2, 0, math.pi), extrude=0.002,
              collection=NEIGHBOR, bold=True)
    text_mesh("Rear_HouseSign_EN", "HOSHIMI-SO", 0.036, (0.95, 3.517, 2.40),
              matte("#7b6145"), rot=(math.pi / 2, 0, math.pi), extrude=0.001,
              collection=NEIGHBOR)
    # Back door, canopy, light and step.
    box("Rear_DoorFrame", (0.68, 0.032, 1.52), (2.72, 3.495, 0.92),
        matte("#354541"), bevel=0.012, collection=NEIGHBOR, outline=True)
    box("Rear_Door", (0.56, 0.022, 1.38), (2.72, 3.512, 0.90),
        matte("#586d66"), bevel=0.009, collection=NEIGHBOR)
    box("Rear_DoorWindow", (0.22, 0.012, 0.36), (2.72, 3.525, 1.31),
        emissive("#ffcf90", 1.25), collection=NEIGHBOR)
    cylinder("Rear_DoorHandle", 0.018, 0.16, (2.91, 3.530, 0.96),
             MAT["steel"], rot=(0, math.pi / 2, 0), collection=NEIGHBOR,
             vertices=8)
    box("Rear_DoorCanopy", (0.86, 0.12, 0.045), (2.72, 3.540, 1.72),
        matte("#3d4541"), bevel=0.008, collection=NEIGHBOR, outline=True)
    box("Rear_DoorStep", (0.78, 0.105, 0.055), (2.72, 3.545, 0.18),
        matte("#858b80"), bevel=0.008, collection=NEIGHBOR, outline=True)
    box("Rear_DoorLampArm", (0.055, 0.15, 0.045), (2.72, 3.515, 1.90),
        MAT["darksteel"], collection=NEIGHBOR)
    box("Rear_DoorLamp", (0.14, 0.10, 0.075), (2.72, 3.555, 1.885),
        emissive("#ffd098", 2.1), collection=NEIGHBOR)
    box("Rear_DoorSign", (0.56, 0.025, 0.17), (2.72, 3.515, 1.96),
        matte("#f0e2be"), bevel=0.006, collection=NEIGHBOR, outline=True)
    text_mesh("Rear_DoorSign_Text", "勝手口 / STAFF ONLY", 0.033,
              (2.72, 3.532, 1.96), matte("#4b5b52"),
              rot=(math.pi / 2, 0, math.pi), extrude=0.001, collection=NEIGHBOR)
    # Utility cluster: meter box, conduit, AC, crates and bottles.
    box("Rear_MeterBox", (0.34, 0.050, 0.40), (0.04, 3.505, 1.34),
        matte("#9da69c"), bevel=0.01, collection=NEIGHBOR, outline=True)
    box("Rear_MeterFace", (0.24, 0.018, 0.27), (0.04, 3.535, 1.35),
        matte("#394b4a"), collection=NEIGHBOR)
    cylinder("Rear_MeterDial", 0.055, 0.012, (0.04, 3.547, 1.39),
             emissive("#72d6c8", 1.2), rot=(math.pi / 2, 0, 0),
             collection=NEIGHBOR, vertices=14)
    for i, (px, pz) in enumerate(((0.23, 1.02), (0.23, 0.74), (0.23, 0.46))):
        box(f"Rear_Conduit_{i}", (0.020, 0.018, 0.24), (px, 3.520, pz),
            MAT["steel"], collection=NEIGHBOR)
    box("Rear_ACBracket", (0.60, 0.08, 0.035), (1.94, 3.525, 2.00),
        MAT["darksteel"], collection=NEIGHBOR)
    box("Rear_AC", (0.52, 0.075, 0.37), (1.94, 3.545, 2.22),
        matte("#c9cdc3"), bevel=0.018, collection=NEIGHBOR, outline=True)
    cylinder("Rear_ACFan", 0.13, 0.018, (1.94, 3.586, 2.22),
             matte("#4c5857"), rot=(math.pi / 2, 0, 0),
             collection=NEIGHBOR, vertices=18)
    for i in range(2):
        box(f"Rear_ACSlat_{i}", (0.28, 0.012, 0.012),
            (1.94, 3.592, 2.31 + i * 0.04), matte("#919781"),
            collection=NEIGHBOR)
    box("Rear_ACDrip", (0.035, 0.035, 0.22), (2.08, 3.52, 1.80),
        MAT["steel"], collection=NEIGHBOR)
    # Small balcony / laundry line under the warm window.
    box("Rear_Balcony", (0.84, 0.110, 0.045), (0.47, 3.535, 1.56),
        matte("#727b73"), bevel=0.008, collection=NEIGHBOR, outline=True)
    for i in range(3):
        box(f"Rear_BalconyRail_{i}", (0.018, 0.018, 0.34),
            (0.18 + i * 0.29, 3.525, 1.74), matte("#a0a398"),
            collection=NEIGHBOR)
    box("Rear_LaundryPole", (0.74, 0.018, 0.018), (0.47, 3.540, 1.83),
        MAT["steel"], collection=NEIGHBOR)
    for i, (col, w) in enumerate((("#d7d2c1", 0.16), ("#8caeb0", 0.12),
                                  ("#ba7f76", 0.11))):
        box(f"Rear_Laundry_{i}", (w, 0.012, 0.30),
            (0.22 + i * 0.23, 3.548, 1.68), matte(col),
            collection=NEIGHBOR)
    # Low clutter along the base: crates, recycling and a gas bottle.
    for i in range(2):
        box(f"Rear_Crate_{i}", (0.38, 0.12, 0.20),
            (1.42 + i * 0.02, 3.545, 0.28 + i * 0.18), matte("#a98251"),
            bevel=0.008, collection=NEIGHBOR, outline=True)
    cylinder("Rear_GasBottle", 0.10, 0.42, (2.08, 3.545, 0.36),
             matte("#88928c"), collection=NEIGHBOR, vertices=14, outline=True)
    cylinder("Rear_GasCap", 0.045, 0.065, (2.08, 3.545, 0.60),
             MAT["steel"], collection=NEIGHBOR, vertices=10)
    cylinder("Rear_Bin", 0.115, 0.30, (3.10, 3.55, 0.30),
             matte("#5d716a"), collection=NEIGHBOR, vertices=12, outline=True)
    for i, (txt, col) in enumerate((("資源ごみ", "#d7c697"), ("火の用心", "#c46d5f"))):
        box(f"Rear_Poster_{i}", (0.28, 0.012, 0.20),
            (0.06 + i * 0.33, 3.510, 1.06), matte(col),
            collection=NEIGHBOR)
        text_mesh(f"Rear_Poster_Text_{i}", txt, 0.038,
                  (0.06 + i * 0.33, 3.525, 1.06), matte("#5b493b"),
                  rot=(math.pi / 2, 0, math.pi), extrude=0.001,
                  collection=NEIGHBOR)
    # A string of warm bulbs under the eaves.
    cable_pts = [(-0.12, 3.57, 2.40), (1.55, 3.57, 2.28), (3.36, 3.57, 2.40)]
    curve_tube("Rear_BulbString", cable_pts, 0.005, matte("#282b2a"),
               collection=NEIGHBOR)
    for i in range(9):
        bx = -0.08 + i * 0.42
        t = i / 8.0
        bz = 2.40 - math.sin(t * math.pi) * 0.12
        sphere(f"Rear_Bulb_{i}", 0.028, (bx, 3.575, bz),
               emissive("#ffd49a", 1.8), collection=NEIGHBOR,
               segments=8, rings=6)
    # A small neon blade above the door adds a saturated edge and a magenta pool.
    box("Rear_NeonArm", (0.18, 0.055, 0.035), (3.26, 3.52, 2.30),
        MAT["darksteel"], collection=NEIGHBOR)
    box("Rear_NeonSign", (0.18, 0.060, 0.52), (3.26, 3.55, 2.05),
        matte("#2b202e"), bevel=0.012, collection=NEIGHBOR, outline=True)
    box("Rear_NeonFace", (0.13, 0.016, 0.44), (3.26, 3.586, 2.05),
        emissive("#ff8ab0", 1.8), collection=NEIGHBOR)
    text_mesh("Rear_NeonText", "24", 0.11, (3.26, 3.598, 2.12),
              matte("#3a2031"), rot=(math.pi / 2, 0, math.pi),
              extrude=0.002, collection=NEIGHBOR, bold=True)
    text_mesh("Rear_NeonSub", "H", 0.09, (3.26, 3.598, 1.98),
              matte("#3a2031"), rot=(math.pi / 2, 0, math.pi),
              extrude=0.002, collection=NEIGHBOR, bold=True)
    # A lit side panel on the store's exposed right wall (visible while orbiting).
    box("Store_SideSign", (0.055, 1.00, 0.40), (2.71, 0.62, 2.16),
        matte("#234d47"), bevel=0.012, collection=STORE, outline=True)
    box("Store_SideSignFace", (0.020, 0.88, 0.30), (2.742, 0.62, 2.16),
        emissive("#f7e8c3", 1.35), collection=STORE)
    text_mesh("Store_SideSignText", "星あかりマート", 0.080,
              (2.757, 0.62, 2.18), matte("#285b53"),
              rot=(math.pi / 2, 0, math.pi / 2), extrude=0.001,
              collection=STORE, bold=True)
    # Rear-facing rooftop sign, visible above the neighbour's roof from behind.
    for side in (-1, 1):
        box(f"Store_RearSignLeg_{side}", (0.055, 0.055, 0.72),
            (0.78 + side * 0.56, 1.68, 3.02), MAT["darksteel"],
            collection=STORE, outline=True)
    box("Store_RearSignCabinet", (1.92, 0.18, 0.62), (1.20, 1.62, 3.38),
        matte("#1b3932"), bevel=0.022, collection=STORE, outline=True)
    box("Store_RearSignFace", (1.74, 0.020, 0.50), (1.20, 1.718, 3.38),
        emissive("#fff0ce", 1.85), collection=STORE)
    text_mesh("Store_RearSign_JP", "星あかりマート", 0.16,
              (1.20, 1.731, 3.45), matte("#26564f"),
              rot=(math.pi / 2, 0, math.pi), extrude=0.003,
              collection=STORE, bold=True)
    text_mesh("Store_RearSign_Sub", "24H  ·  PARKING  →", 0.050,
              (1.20, 1.731, 3.31), matte("#796545"),
              rot=(math.pi / 2, 0, math.pi), extrude=0.001,
              collection=STORE)
    box("Store_RearSignNeon", (1.98, 0.018, 0.020), (1.20, 1.729, 3.09),
        emissive("#88e7c9", 1.3), collection=STORE)
    # Neighbour rooftop clutter: water tank, antenna and a few plants.
    box("Neighbor_TankBase", (0.92, 0.72, 0.08), (0.28, 2.72, 2.82),
        matte("#4b5552"), bevel=0.01, collection=NEIGHBOR, outline=True)
    cylinder("Neighbor_WaterTank", 0.24, 0.60, (0.28, 2.72, 3.12),
             matte("#9ca7a1"), collection=NEIGHBOR, vertices=18,
             outline=True)
    cylinder("Neighbor_TankLid", 0.255, 0.035, (0.28, 2.72, 3.44),
             matte("#76837f"), collection=NEIGHBOR, vertices=18)
    box("Neighbor_AntennaBase", (0.10, 0.10, 0.10), (3.15, 2.72, 2.83),
        MAT["darksteel"], collection=NEIGHBOR)
    cylinder("Neighbor_Antenna", 0.018, 1.40, (3.15, 2.72, 3.53),
             MAT["steel"], collection=NEIGHBOR, vertices=8)
    for i in range(2):
        box(f"Neighbor_AntennaBar_{i}", (0.54, 0.015, 0.015),
            (3.15, 2.72, 3.38 + i * 0.22), MAT["steel"],
            collection=NEIGHBOR)
    sphere("Neighbor_AntennaBeacon", 0.035, (3.15, 2.72, 4.23),
           emissive("#ef6b5f", 0.8), collection=NEIGHBOR,
           segments=8, rings=6)
    for i, (px, py, col) in enumerate(((1.95, 3.38, "#5a8c68"),
                                        (2.18, 3.38, "#4f8061"))):
        cylinder(f"Neighbor_RoofPot_{i}", 0.07, 0.16,
                 (px, py, 2.88), matte("#a36c4e"),
                 collection=NEIGHBOR, vertices=10)
        sphere(f"Neighbor_RoofPlant_{i}", 0.11, (px, py, 3.02),
               matte(col), collection=NEIGHBOR, segments=10, rings=6)
    # Lighting for the rear service elevation.
    point_light("L_Back_WarmWash", (1.35, 3.74, 2.10), 36,
                (1.0, 0.66, 0.36), 1.6, LIGHTS)
    point_light("L_Back_Door", (2.72, 3.66, 1.92), 18,
                (1.0, 0.70, 0.40), 0.45, LIGHTS)
    point_light("L_Back_Cool", (0.10, 3.62, 1.90), 13,
                (0.44, 0.70, 1.0), 0.55, LIGHTS)
    point_light("L_Back_Sign", (1.20, 1.94, 3.32), 14,
                (0.78, 1.0, 0.88), 0.55, LIGHTS)
    point_light("L_Back_Neon", (3.26, 3.72, 2.00), 8,
                (1.0, 0.30, 0.55), 0.35, LIGHTS)
    # Side elevation of the neighbour, visible when orbiting left of the shop.
    side_x = -0.192
    box("Neighbor_SideWindowFrame", (0.030, 0.64, 0.52),
        (side_x, 2.67, 1.95), matte("#35443f"), bevel=0.008,
        collection=NEIGHBOR, outline=True)
    plane("Neighbor_SideWindowGlow", (0.52, 0.40),
          (side_x - 0.016, 2.67, 1.95), emissive("#ffd39c", 1.15),
          rot=(math.pi / 2, 0, -math.pi / 2), collection=NEIGHBOR)
    box("Neighbor_SideWindowMullion", (0.014, 0.018, 0.40),
        (side_x - 0.025, 2.67, 1.95), matte("#3a4843"),
        collection=NEIGHBOR)
    box("Neighbor_SideWindowAwning", (0.13, 0.74, 0.035),
        (side_x - 0.055, 2.67, 2.25), matte("#d9c49d"),
        rot=(0, math.radians(-14), 0), bevel=0.006,
        collection=NEIGHBOR, outline=True)
    text_mesh("Neighbor_SideName", "星見荘", 0.070,
              (side_x - 0.035, 2.67, 2.43), matte("#42554c"),
              rot=(math.pi / 2, 0, -math.pi / 2), extrude=0.001,
              collection=NEIGHBOR, bold=True)
    box("Neighbor_SideMeter", (0.035, 0.26, 0.34),
        (side_x - 0.036, 3.10, 1.16), matte("#99a096"),
        bevel=0.008, collection=NEIGHBOR, outline=True)
    box("Neighbor_SideMeterFace", (0.014, 0.18, 0.22),
        (side_x - 0.057, 3.10, 1.18), matte("#3d4d4a"),
        collection=NEIGHBOR)
    cylinder("Neighbor_SidePipe", 0.025, 2.28,
             (side_x - 0.030, 3.38, 1.36), MAT["steel"],
             collection=NEIGHBOR, vertices=9)
    for i in range(2):
        box(f"Neighbor_SideCrates_{i}", (0.30, 0.32, 0.19),
            (-0.55, 2.42 + i * 0.04, WALK_Z + 0.11 + i * 0.18),
            matte("#a98754" if i == 0 else "#8f7348"),
            bevel=0.008, collection=NEIGHBOR, outline=True)
    cylinder("Neighbor_SideLantern", 0.10, 0.24,
             (-0.60, 2.80, 1.24), emissive("#ffc178", 1.9),
             collection=NEIGHBOR, vertices=14, outline=True)
    for i in range(2):
        cylinder(f"Neighbor_SideLanternRing_{i}", 0.105, 0.020,
                 (-0.60, 2.80, 1.14 + i * 0.20), MAT["ink"],
                 collection=NEIGHBOR, vertices=14)
    point_light("L_Back_Side", (-0.55, 2.55, 1.65), 12,
                (1.0, 0.60, 0.32), 0.45, LIGHTS)
    # Dress the low rear boundary walls too; these become foreground when the
    # model is viewed from behind and were otherwise flat black panels.
    box("BackWall_ServiceDoor", (0.74, 0.026, 0.94), (-2.82, 3.515, 0.72),
        matte("#465751"), bevel=0.01, collection=NEIGHBOR, outline=True)
    box("BackWall_ServiceDoorFace", (0.63, 0.014, 0.82), (-2.82, 3.532, 0.72),
        matte("#5d6e66"), bevel=0.006, collection=NEIGHBOR)
    cylinder("BackWall_DoorHandle", 0.018, 0.12, (-2.55, 3.545, 0.73),
             MAT["steel"], rot=(0, math.pi / 2, 0), collection=NEIGHBOR,
             vertices=8)
    box("BackWall_Sign", (0.52, 0.02, 0.16), (-2.82, 3.54, 1.32),
        matte("#e3d7b6"), bevel=0.006, collection=NEIGHBOR, outline=True)
    text_mesh("BackWall_Sign_Text", "関係者以外立入禁止", 0.034,
              (-2.82, 3.554, 1.32), matte("#73594a"),
              rot=(math.pi / 2, 0, math.pi), extrude=0.001,
              collection=NEIGHBOR)
    box("BackWall_Lamp", (0.15, 0.09, 0.07), (-2.82, 3.55, 1.50),
        emissive("#ffd29b", 1.9), collection=NEIGHBOR)
    point_light("L_Back_ServiceDoor", (-2.82, 3.68, 1.45), 10,
                (1.0, 0.66, 0.39), 0.35, LIGHTS)
    # A wooden service gate in the low wall, with a small warm lantern.
    gate_x = (-1.92, -0.34)
    for side, gx in enumerate(gate_x):
        box(f"BackGate_Post_{side}", (0.08, 0.08, 0.98),
            (gx, 3.51, 0.62), matte("#5f4b37"), bevel=0.008,
            collection=NEIGHBOR, outline=True)
    for i in range(7):
        gx = gate_x[0] + (gate_x[1] - gate_x[0]) * i / 6
        box(f"BackGate_Slat_{i}", (0.055, 0.026, 0.64),
            (gx, 3.52, 0.51), matte("#765c42"),
            collection=NEIGHBOR)
    box("BackGate_Top", (1.70, 0.07, 0.07), (-1.13, 3.51, 0.98),
        matte("#5f4b37"), bevel=0.008, collection=NEIGHBOR, outline=True)
    box("BackGate_Sign", (0.60, 0.02, 0.16), (-1.13, 3.545, 1.09),
        matte("#e2d4ad"), bevel=0.006, collection=NEIGHBOR, outline=True)
    text_mesh("BackGate_Sign_Text", "星あかりマート 裏口", 0.031,
              (-1.13, 3.558, 1.09), matte("#75533d"),
              rot=(math.pi / 2, 0, math.pi), extrude=0.001,
              collection=NEIGHBOR)
    cylinder("BackGate_Lantern", 0.085, 0.19, (-1.83, 3.54, 1.30),
             emissive("#ffc27b", 1.9), collection=NEIGHBOR, vertices=12,
             outline=True)
    point_light("L_Back_Gate", (-1.70, 3.66, 1.28), 13,
                (1.0, 0.59, 0.31), 0.4, LIGHTS)
    for i, (px, pz, s) in enumerate(((-2.35, 0.34, 0.8), (-2.10, 0.30, 1.0),
                                      (-0.15, 0.31, 0.75))):
        cylinder(f"RearPlanter_{i}", 0.10 * s, 0.20 * s,
                 (px, 3.54, WALK_Z + 0.10 * s), matte("#9f664d"),
                 collection=NEIGHBOR, vertices=10)
        sphere(f"RearPlanter_Leaf_{i}", 0.13 * s, (px, 3.54, WALK_Z + 0.26 * s),
               matte("#537451"), collection=NEIGHBOR, segments=10, rings=6)
    # Right side elevation of the neighbour (seen from the rear-right orbit).
    right_x = 3.492
    box("Neighbor_RightWindowFrame", (0.030, 0.60, 0.48),
        (right_x, 2.55, 1.98), matte("#35443f"), bevel=0.008,
        collection=NEIGHBOR, outline=True)
    plane("Neighbor_RightWindowGlow", (0.48, 0.36),
          (right_x + 0.018, 2.55, 1.98), emissive("#ffd3a0", 1.05),
          rot=(math.pi / 2, 0, math.pi / 2), collection=NEIGHBOR)
    box("Neighbor_RightWindowSill", (0.080, 0.68, 0.030),
        (right_x + 0.02, 2.55, 1.72), matte("#768077"),
        collection=NEIGHBOR)
    box("Neighbor_RightAC", (0.080, 0.44, 0.28),
        (right_x + 0.02, 3.06, 1.26), matte("#bcc2b8"),
        bevel=0.01, collection=NEIGHBOR, outline=True)
    cylinder("Neighbor_RightFan", 0.10, 0.020, (right_x + 0.066, 3.06, 1.26),
             matte("#4e5b58"), rot=(0, math.pi / 2, 0),
             collection=NEIGHBOR, vertices=16)
    cylinder("Neighbor_RightPipe", 0.024, 2.15,
             (right_x + 0.026, 2.05, 1.32), MAT["steel"],
             collection=NEIGHBOR, vertices=9)
    box("Neighbor_RightPoster", (0.014, 0.30, 0.22),
        (right_x + 0.018, 2.18, 0.82), matte("#d8c38e"),
        collection=NEIGHBOR)
    text_mesh("Neighbor_RightPosterText", "火の用心", 0.040,
              (right_x + 0.030, 2.18, 0.82), matte("#594739"),
              rot=(math.pi / 2, 0, math.pi / 2), extrude=0.001,
              collection=NEIGHBOR)
    box("Neighbor_RightLamp", (0.05, 0.16, 0.06),
        (right_x + 0.055, 3.35, 2.05), emissive("#ffd39b", 1.8),
        collection=NEIGHBOR)
    point_light("L_Back_Right", (3.66, 2.0, 2.40), 8,
                (1.0, 0.70, 0.40), 0.4, LIGHTS)
    # A slim wet glow strip along the rear edge keeps the base from going black.
    plane("Rear_LightSpill", (3.20, 0.22), (1.58, 3.52, 0.205),
          soft_glow("#ffb466", 0.8, falloff=0.54), collection=FX)


# ---------------------------------------------------------------------------
# Rain / FX / lighting / camera / compositor
# ---------------------------------------------------------------------------
def build_rain_and_fx():
    # Rain streaks as one lightweight mesh, render-only.
    import bmesh
    mesh = bpy.data.meshes.new("RAIN_STREAKS")
    bm = bmesh.new()
    rain_mat = decal("#c8e9ff", alpha=0.10, strength=0.8)
    for i in range(680):
        x = RNG.uniform(-3.5, 3.5)
        y = RNG.uniform(-3.5, 3.5)
        z = RNG.uniform(0.4, 4.8)
        length = RNG.uniform(0.16, 0.62)
        width = RNG.uniform(0.004, 0.009)
        yaw = RNG.uniform(0, math.pi)
        dx = math.cos(yaw) * width
        dy = math.sin(yaw) * width
        v0 = bm.verts.new((x - dx, y - dy, z))
        v1 = bm.verts.new((x + dx, y + dy, z))
        v2 = bm.verts.new((x + dx * 1.4, y + dy * 1.4, z + length))
        v3 = bm.verts.new((x - dx * 1.4, y - dy * 1.4, z + length))
        bm.faces.new((v0, v1, v2, v3))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("RAIN_STREAKS", mesh)
    FX.objects.link(obj)
    mesh.materials.append(rain_mat)
    tag(obj, outline=False, kind="decal")
    # Eaves drips: thin vertical streaks and tiny splash discs.
    for i, (x, y) in enumerate(((-0.2, -1.34), (0.65, -1.38), (1.55, -1.38),
                                 (2.35, -1.38), (-0.96, 0.15), (-0.96, 0.92))):
        top = CANOPY_Z - 0.05
        bottom = RNG.uniform(0.30, 1.25)
        curve_tube(f"EaveDrip_{i}", [(x, y, top), (x, y, bottom)], 0.009,
                   decal("#d5f0ff", alpha=0.36, strength=1.0), collection=FX)
        torus(f"EaveSplash_{i}", 0.035, 0.006,
              (x, y + 0.02, WALK_Z + 0.04), decal("#cfeeff", 0.22, 0.8),
              collection=FX, major_seg=12, minor_seg=4)
    # Rain streaks on the storefront glass, kept sparse so the interior stays legible.
    for i in range(11):
        x = RNG.uniform(0.50, 2.55)
        z = RNG.uniform(0.58, 2.20)
        h = RNG.uniform(0.10, 0.42)
        curve_tube(f"GlassStreak_{i}", [(x, STORE_Y0 - 0.012, z),
                                       (x + RNG.uniform(-0.025, 0.025),
                                        STORE_Y0 - 0.012, z - h)],
                   0.006, decal("#e1f6ff", 0.35, 0.9), collection=FX)
    # Low mist ribbons around the base edges, very subtle.
    for i, (x, y, sx, sy, a) in enumerate((
        (-1.7, -2.95, 2.8, 0.7, 0.055),
        (2.3, -1.3, 1.6, 0.55, 0.04),
        (-2.6, 1.8, 0.8, 2.4, 0.035),
    )):
        plane(f"Mist_{i}", (sx, sy), (x, y, 0.06),
              decal("#a8c9e8", alpha=a, strength=0.35), collection=FX)
    # Soft, additive light pools. These do the heavy lifting for the anime wet-night
    # look and are reproduced with canvas gradients in the web viewer.
    glow_pools = [
        ("Glow_Storefront", 1.20, -1.16, 4.0, 1.55, "#ff9b52", 1.65, WALK_Z + 0.035),
        ("Glow_Entrance", -0.10, -1.20, 1.8, 1.0, "#ffc269", 1.55, WALK_Z + 0.040),
        ("Glow_Vending_Cyan", -1.68, -1.42, 2.2, 1.25, "#55ddff", 1.55, WALK_Z + 0.038),
        ("Glow_Vending_Warm", -1.20, -1.40, 1.5, 0.9, "#ff905b", 1.05, WALK_Z + 0.041),
        ("Glow_StreetLamp", -2.15, -1.85, 2.7, 2.0, "#ffb45f", 1.15, WALK_Z + 0.036),
        ("Glow_Alley", 3.12, -0.42, 1.2, 1.1, "#ff955c", 0.95, WALK_Z + 0.035),
    ]
    for name, x, y, sx, sy, color, strength, z in glow_pools:
        plane(name, (sx, sy), (x, y, z), soft_glow(color, strength),
              collection=FX)
    # Long saturated reflection streaks on the asphalt, a signature anime-night cue.
    for i, (x, y, sx, sy, color, strength) in enumerate((
        (0.65, -2.20, 0.38, 2.0, "#ff9d50", 1.85),
        (1.65, -2.58, 0.26, 1.55, "#ffd07c", 1.5),
        (-1.42, -2.58, 0.30, 1.35, "#55ddff", 1.75),
        (2.38, -2.02, 0.22, 1.10, "#ff6f9a", 1.35),
        (-2.18, -3.15, 0.18, 0.85, "#ffa85b", 1.20),
    )):
        plane(f"NeonReflection_{i}", (sx, sy), (x, y, 0.044),
              soft_glow(color, strength, falloff=0.38), collection=FX)
    # Rain drip chain from the canopy edge.
    for i in range(6):
        x = -0.35 + i * 0.5
        cylinder(f"GutterDrop_{i}", 0.012, 0.08, (x, -1.40, CANOPY_Z - 0.04),
                 decal("#d8f4ff", 0.32, 0.9), collection=FX, vertices=6)
    # Low blue ground mist ribbons (soft cards).
    for i, (x, y, sx, sy, a) in enumerate((
        (-2.1, -2.7, 3.6, 1.0, "#5b7fb8"),
        (2.5, 0.4, 1.4, 2.5, "#4e638a"),
    )):
        plane(f"GroundMist_{i}", (sx, sy), (x, y, 0.08),
              soft_glow(a, 0.22, falloff=0.52), collection=FX)


def setup_lighting():
    # Sky / world: deep indigo with a faint blue-violet lift at the horizon.
    world = bpy.data.worlds.new("RainyNightWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    wout = nt.nodes.new("ShaderNodeOutputWorld")
    # Ambient light contribution (cool overcast night).
    bg_light = nt.nodes.new("ShaderNodeBackground")
    bg_light.inputs[0].default_value = (0.008, 0.018, 0.052, 1)
    bg_light.inputs[1].default_value = 0.24
    # Camera-only sky gradient, independent of the ambient lighting.
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mapr = nt.nodes.new("ShaderNodeMapRange")
    mapr.inputs["From Min"].default_value = -1.0
    mapr.inputs["From Max"].default_value = 1.0
    mapr.inputs["To Min"].default_value = 0.0
    mapr.inputs["To Max"].default_value = 1.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "EASE"
    cr.elements[0].position = 0.0
    cr.elements[0].color = srgb("#060812")
    cr.elements[1].position = 0.48
    cr.elements[1].color = srgb("#101b34")
    third = cr.elements.new(0.78)
    third.color = srgb("#1d1d38")
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    bg_cam.inputs[1].default_value = 0.75
    lp = nt.nodes.new("ShaderNodeLightPath")
    mixw = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Incoming"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mapr.inputs["Value"])
    nt.links.new(mapr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg_cam.inputs["Color"])
    nt.links.new(bg_light.outputs["Background"], mixw.inputs[1])
    nt.links.new(bg_cam.outputs["Background"], mixw.inputs[2])
    nt.links.new(lp.outputs["Is Camera Ray"], mixw.inputs[0])
    nt.links.new(mixw.outputs["Shader"], wout.inputs["Surface"])
    # Large cool area light acts as the overcast moon/sky.
    area_light("L_Night_Sky", (-4.6, -2.8, 6.2), (math.radians(26), 0, math.radians(-35)),
               105, (0.38, 0.54, 0.92), (6.0, 5.0), LIGHTS)
    # Rim light from the right, to separate the shop from the dark background.
    area_light("L_Cool_Rim", (4.8, 1.8, 4.5), (math.radians(65), 0, math.radians(145)),
               60, (0.44, 0.66, 1.0), (2.5, 1.5), LIGHTS)
    # Warm spill under the canopy (already have many points, add one broad wash).
    area_light("L_Front_Warm_Wash", (0.9, -1.3, 2.0), (math.radians(72), 0, 0),
               95, (1.0, 0.58, 0.27), (3.0, 0.8), LIGHTS)
    # Neighbour window warmth.
    point_light("L_Neighbor", (1.65, 1.90, 2.0), 12, (1.0, 0.67, 0.37), 1.0, LIGHTS)
    # Interior fill near the entrance.
    point_light("L_Entrance", (0.00, 0.15, 1.95), 18, (1.0, 0.71, 0.42), 0.55, LIGHTS)
    # Cool footlight at the base edge, adds separation.
    point_light("L_BaseCool", (-2.8, -2.9, 0.20), 10, (0.30, 0.52, 1.0), 0.55, LIGHTS)


def setup_camera_and_render():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 48
    scene.eevee.use_shadows = True
    if hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = True
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 240
    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "None"
    except Exception:
        pass
    scene.view_settings.exposure = -0.60
    scene.render.filepath = os.path.join(ROOT, "renders", "hero.png")
    # Camera: front-left three-quarter, with the whole square base in frame.
    cam_data = bpy.data.cameras.new("HeroCamera")
    cam_data.lens = 51
    cam_data.sensor_width = 36
    cam_data.clip_end = 100
    cam = bpy.data.objects.new("HeroCamera", cam_data)
    CAMCOL.objects.link(cam)
    cam.location = (-4.40, -10.30, 4.20)
    target = bpy.data.objects.new("CameraTarget", None)
    CAMCOL.objects.link(target)
    target.location = (0.28, 0.05, 0.95)
    con = cam.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    scene.camera = cam
    # Freestyle — only major silhouettes and architecture, not every product.
    scene.render.use_freestyle = True
    scene.render.line_thickness_mode = "ABSOLUTE"
    scene.render.line_thickness = 2.0
    fs = bpy.context.view_layer.freestyle_settings
    while fs.linesets:
        fs.linesets.remove(fs.linesets[0])
    ls = fs.linesets.new("InkLines")
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = True
    try:
        ls.crease_angle = math.radians(125)
    except Exception:
        pass
    try:
        ls.select_by_collection = True
        ls.collection = OUTLINE
    except Exception:
        pass
    ink = bpy.data.linestyles.new("Ink")
    ink.color = (0.008, 0.014, 0.030)
    ink.thickness = 2.0
    ls.linestyle = ink
    # Compositor: soft fog glow. Blender 5.2 uses an assigned node group with a
    # Group Output instead of the old scene.node_tree / Composite node.
    scene.use_nodes = True
    ng = bpy.data.node_groups.new("RainyNightCompositor", "CompositorNodeTree")
    ng.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    scene.compositing_node_group = ng
    rl = ng.nodes.new("CompositorNodeRLayers")
    rl.location = (-360, 0)
    glare = ng.nodes.new("CompositorNodeGlare")
    glare.location = (-40, 0)
    try:
        glare.inputs["Type"].default_value = "Fog Glow"
        glare.inputs["Quality"].default_value = "High"
    except Exception:
        pass
    glare.inputs["Threshold"].default_value = 0.62
    glare.inputs["Strength"].default_value = 0.78
    glare.inputs["Size"].default_value = 0.78
    gout = ng.nodes.new("NodeGroupOutput")
    gout.location = (300, 0)
    ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
    ng.links.new(glare.outputs["Image"], gout.inputs["Image"])
    # Use a render view for quick checks in Blender.
    for area in getattr(bpy.context.screen, "areas", []):
        if area.type == "VIEW_3D":
            area.spaces.active.region_3d.view_perspective = "CAMERA"


def setup_animation():
    scene = bpy.context.scene
    scene.frame_set(1)
    # Automatic doors open between 28–58 and close again 118–150.
    for side in ("L", "R"):
        root = bpy.data.objects.get(f"DOOR_{side}")
        if not root:
            continue
        base_x = root.location.x
        # Animate the child mesh parts, not the root, so viewers can move each door.
        children = [o for o in root.children if o.type == "MESH"]
        for child in children:
            x0 = child.location.x
            sign = -1 if side == "L" else 1
            child.location.x = x0
            child.keyframe_insert("location", frame=1)
            child.location.x = x0 + sign * 0.43
            child.keyframe_insert("location", frame=52)
            child.keyframe_insert("location", frame=120)
            child.location.x = x0
            child.keyframe_insert("location", frame=156)
            child.location.x = x0
            child.keyframe_insert("location", frame=240)
    # Subtle sign/tube flicker. The materials are distinct so this affects only accents.
    sign_mat = emissive("#fff2cf", 1.8)
    keyframe_emission(sign_mat, [(1, 1.8), (70, 1.8), (71, 0.8), (72, 1.8),
                                 (178, 1.8), (179, 0.6), (181, 1.8), (240, 1.8)])
    # Traffic-light cycle. Reuse the exact materials created on the signal lamps.
    active, dim = 2.8, 0.18
    red_mat = emissive("#e2584e", dim)
    amber_mat = emissive("#e4b356", 0.15)
    green_mat = emissive("#62bdb0", active)
    keyframe_emission(red_mat, [(1, active), (120, active), (121, dim), (240, dim)])
    keyframe_emission(amber_mat, [(1, dim), (80, dim), (81, active), (120, active),
                                  (121, dim), (240, dim)])
    keyframe_emission(green_mat, [(1, dim), (80, dim), (81, active), (240, active)])
    # Ripple rings slowly expand; they are render-only, so simple scale loops suffice.
    for i, obj in enumerate([o for o in FX.objects if o.name.startswith("PuddleRipple")]):
        start = 1 + (i * 11) % 160
        obj.scale = (0.35, 0.35, 0.35)
        obj.keyframe_insert("scale", frame=start)
        obj.scale = (1.25, 1.25, 1.25)
        obj.keyframe_insert("scale", frame=start + 50)
        obj.scale = (0.35, 0.35, 0.35)
        obj.keyframe_insert("scale", frame=start + 80)
    scene.frame_set(36)


def main():
    build_base()
    build_street()
    build_store_outer()
    build_interior()
    build_street_props()
    build_neighbourhood()
    build_back_elevation()
    build_rain_and_fx()
    setup_lighting()
    setup_camera_and_render()
    setup_animation()
    # Make sure all model objects are linked into WEB_EXPORT (helpers automatically do this).
    for obj in bpy.context.scene.objects:
        if obj.type in {"MESH", "CURVE", "FONT"} and WEB.objects.get(obj.name) is None:
            try:
                WEB.objects.link(obj)
            except RuntimeError:
                pass
    # Render-only effects are excluded from the web export.
    for obj in list(FX.objects):
        if WEB.objects.get(obj.name) is not None:
            WEB.objects.unlink(obj)
    # Name the scene and save.
    scene = bpy.context.scene
    scene.name = "Hoshiakari Mart — Rainy Night"
    # Make the test render output directory.
    os.makedirs(os.path.join(ROOT, "renders"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    mesh_count = sum(1 for o in scene.objects if o.type == "MESH")
    print(f"SCENE_BUILT meshes={mesh_count} objects={len(scene.objects)}")
    print(f"BLEND_SAVED {BLEND_PATH} {os.path.getsize(BLEND_PATH)}")


if __name__ == "__main__":
    main()
