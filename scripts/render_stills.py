"""Render the approved still shots from the saved diorama."""
import bpy
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
res = 640
samples = 16
shot = "hero"
out = os.path.join(ROOT, "renders", "preview.png")
freestyle = True
for i, arg in enumerate(args):
    if arg == "--res":
        res = int(args[i + 1])
    elif arg == "--samples":
        samples = int(args[i + 1])
    elif arg == "--shot":
        shot = args[i + 1]
    elif arg == "--out":
        out = args[i + 1]
        if not os.path.isabs(out):
            out = os.path.join(ROOT, out)
    elif arg == "--no-freestyle":
        freestyle = False

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = samples
scene.render.resolution_x = res
scene.render.resolution_y = res
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.film_transparent = False
scene.render.use_freestyle = freestyle
scene.frame_set(36)
scene.render.filepath = out

cam = scene.camera
target = bpy.data.objects.get("CameraTarget")
shot_exposure = -0.60
if shot == "hero":
    cam.location = (-4.40, -10.30, 4.20)
    target.location = (0.28, 0.05, 0.95)
    cam.data.lens = 51
elif shot == "interior":
    cam.location = (0.40, -5.20, 1.70)
    target.location = (1.00, 0.15, 1.10)
    cam.data.lens = 45
    shot_exposure = -0.80
elif shot == "street":
    cam.location = (-5.0, -8.2, 2.3)
    target.location = (0.55, -0.1, 1.10)
    cam.data.lens = 40
    shot_exposure = -0.86
elif shot == "left":
    cam.location = (-8.2, -4.8, 4.1)
    target.location = (0.4, 0.2, 1.2)
    cam.data.lens = 60
elif shot == "top":
    cam.location = (-3.5, -6.0, 10.5)
    target.location = (0.2, 0.3, 0.5)
    cam.data.lens = 55
elif shot == "back":
    cam.location = (6.6, 10.2, 4.4)
    target.location = (0.9, 0.5, 1.2)
    cam.data.lens = 44
    shot_exposure = -0.30
elif shot == "back_left":
    cam.location = (-5.3, 9.8, 4.2)
    target.location = (0.5, 0.5, 1.2)
    cam.data.lens = 44
    shot_exposure = -0.35

scene.view_settings.exposure = shot_exposure
os.makedirs(os.path.dirname(out), exist_ok=True)
print("RENDERING", shot, res, samples, out, "freestyle", freestyle)
bpy.ops.render.render(write_still=True)
print("RENDER_DONE", os.path.exists(out), os.path.getsize(out) if os.path.exists(out) else 0)
