import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { OutlinePass } from "three/examples/jsm/postprocessing/OutlinePass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import glbBytes from "../../dist/scene.glb";

/* ------------------------------------------------------------------------- */
/* Setup                                                                      */
/* ------------------------------------------------------------------------- */
const canvas = document.getElementById("scene");
const app = document.getElementById("app");
const loading = document.getElementById("loading");
const errorOverlay = document.getElementById("error");
const errorText = document.getElementById("errorText");
const debugEl = document.getElementById("debug");
const hintEl = document.getElementById("hint");
const params = new URLSearchParams(window.location.search);
const isDebug = params.get("debug") === "1";
const hideUiAtStart = params.get("ui") === "0";
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const HERO_TARGET = new THREE.Vector3(0.28, 0.95, -0.05);
const CAMERA_PRESETS = {
  hero: {
    position: new THREE.Vector3(-5.3, 4.9, 12.1),
    target: new THREE.Vector3(0.25, 0.68, -0.10),
    fov: 39,
  },
  street: {
    position: new THREE.Vector3(-5.2, 2.1, 8.4),
    target: new THREE.Vector3(0.55, 1.20, 0.90),
    fov: 42,
  },
  interior: {
    position: new THREE.Vector3(0.75, 2.20, 6.15),
    target: new THREE.Vector3(1.00, 1.30, 0.05),
    fov: 40,
  },
  top: {
    position: new THREE.Vector3(-4.2, 10.2, 8.2),
    target: new THREE.Vector3(0.25, 0.65, -0.12),
    fov: 38,
  },
  back: {
    position: new THREE.Vector3(6.4, 4.8, -11.9),
    target: new THREE.Vector3(0.80, 1.15, -1.60),
    fov: 42,
  },
};

function showError(message) {
  if (errorText) errorText.textContent = message;
  if (errorOverlay) errorOverlay.hidden = false;
  if (loading) loading.classList.add("is-done");
  window.__VIEWER_ERROR__ = message;
}

let renderer;
try {
  renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: "high-performance",
  });
} catch (err) {
  showError("当前浏览器无法创建 WebGL2 上下文。请用最新版 Chrome 或 Edge 打开。");
  throw err;
}

renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.65));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.68;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x07101b, 0.011);

const camera = new THREE.PerspectiveCamera(
  CAMERA_PRESETS.hero.fov,
  window.innerWidth / window.innerHeight,
  0.06,
  120
);
camera.position.copy(CAMERA_PRESETS.hero.position);

const controls = new OrbitControls(camera, canvas);
controls.target.copy(CAMERA_PRESETS.hero.target);

controls.enableDamping = true;
controls.dampingFactor = 0.065;
controls.rotateSpeed = 0.52;
controls.zoomSpeed = 0.75;
controls.panSpeed = 0.55;
controls.minDistance = 4.2;
controls.maxDistance = 22;
controls.minPolarAngle = 0.22;
controls.maxPolarAngle = 1.46;
controls.screenSpacePanning = false;
controls.autoRotate = false;
controls.autoRotateSpeed = 0.28;
controls.update();

/* ------------------------------------------------------------------------- */
/* Sky / atmosphere                                                          */
/* ------------------------------------------------------------------------- */
const sky = new THREE.Mesh(
  new THREE.SphereGeometry(55, 48, 24),
  new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
    uniforms: {
      uTop: { value: new THREE.Color(0x09101d) },
      uBottom: { value: new THREE.Color(0x03060d) },
      uGlow: { value: new THREE.Color(0x362b4a) },
    },
    vertexShader: `
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform vec3 uTop;
      uniform vec3 uBottom;
      uniform vec3 uGlow;
      varying vec3 vDir;
      void main() {
        float h = clamp(vDir.y * 0.5 + 0.5, 0.0, 1.0);
        vec3 col = mix(uBottom, uTop, smoothstep(0.02, 0.92, h));
        float horizon = exp(-pow((h - 0.40) * 4.6, 2.0));
        col += uGlow * horizon * 0.55;
        float cloud = sin(vDir.x * 8.0 + vDir.z * 5.0 + vDir.y * 17.0) * 0.5 + 0.5;
        cloud *= sin(vDir.z * 19.0 - vDir.y * 11.0) * 0.5 + 0.5;
        col += vec3(0.017, 0.021, 0.038) * cloud * 0.35;
        gl_FragColor = vec4(col, 1.0);
      }
    `,
  })
);
sky.renderOrder = -20;
scene.add(sky);

// A soft, mostly invisible shadow plate under the miniature.
function makeShadowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const ctx = c.getContext("2d");
  const g = ctx.createRadialGradient(128, 128, 8, 128, 128, 126);
  g.addColorStop(0, "rgba(0,0,0,0.58)");
  g.addColorStop(0.48, "rgba(0,0,0,0.26)");
  g.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 256, 256);
  return new THREE.CanvasTexture(c);
}
const floorShadow = new THREE.Mesh(
  new THREE.PlaneGeometry(9.2, 9.2),
  new THREE.MeshBasicMaterial({
    map: makeShadowTexture(),
    transparent: true,
    depthWrite: false,
    color: 0x000000,
    opacity: 0.72,
  })
);
floorShadow.rotation.x = -Math.PI / 2;
floorShadow.position.set(0, -0.47, 0);
scene.add(floorShadow);

/* ------------------------------------------------------------------------- */
/* Environment map for wet surfaces and glass                                 */
/* ------------------------------------------------------------------------- */
function makeEnvironment() {
  const c = document.createElement("canvas");
  c.width = 1024;
  c.height = 512;
  const ctx = c.getContext("2d");
  const bg = ctx.createLinearGradient(0, 0, 0, 512);
  bg.addColorStop(0, "#03060e");
  bg.addColorStop(0.44, "#071326");
  bg.addColorStop(0.58, "#11243e");
  bg.addColorStop(1, "#03050a");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, 1024, 512);
  const blobs = [
    [310, 292, 165, "rgba(255,174,92,0.38)"],
    [520, 302, 110, "rgba(102,225,235,0.19)"],
    [760, 282, 125, "rgba(255,104,164,0.18)"],
    [125, 300, 90, "rgba(124,170,255,0.16)"],
  ];
  for (const [x, y, r, color] of blobs) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, color);
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  // Subtle horizon smear so glass picks up a night-city reflection.
  const sm = ctx.createLinearGradient(0, 250, 0, 330);
  sm.addColorStop(0, "rgba(160,180,255,0)");
  sm.addColorStop(0.5, "rgba(160,180,255,0.16)");
  sm.addColorStop(1, "rgba(160,180,255,0)");
  ctx.fillStyle = sm;
  ctx.fillRect(0, 250, 1024, 80);
  const tex = new THREE.CanvasTexture(c);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const env = pmrem.fromEquirectangular(tex).texture;
  pmrem.dispose();
  tex.dispose();
  return env;
}
scene.environment = makeEnvironment();
scene.environmentIntensity = 0.8;

/* ------------------------------------------------------------------------- */
/* Lighting                                                                   */
/* ------------------------------------------------------------------------- */
scene.add(new THREE.AmbientLight(0x1b2a45, 0.22));
const hemi = new THREE.HemisphereLight(0x6f8fca, 0x0a0d12, 0.38);
scene.add(hemi);

const moon = new THREE.DirectionalLight(0x9cbbff, 0.82);
moon.position.set(-6.0, 10.5, 7.0);
moon.target.position.set(0.1, 0.6, -0.3);
moon.castShadow = true;
moon.shadow.mapSize.set(2048, 2048);
moon.shadow.camera.left = -8;
moon.shadow.camera.right = 8;
moon.shadow.camera.top = 8;
moon.shadow.camera.bottom = -8;
moon.shadow.camera.near = 0.5;
moon.shadow.camera.far = 35;
moon.shadow.bias = -0.0005;
moon.shadow.normalBias = 0.025;
scene.add(moon, moon.target);

const coolRim = new THREE.DirectionalLight(0x5f86ff, 0.22);
coolRim.position.set(5.0, 3.5, -5.0);
scene.add(coolRim);

function addPoint(name, x, y, z, color, intensity, distance, decay = 2) {
  const light = new THREE.PointLight(color, intensity, distance, decay);
  light.name = name;
  light.position.set(x, y, z);
  scene.add(light);
  return light;
}

const storeLights = [
  addPoint("L_StoreFront", 0.7, 2.10, 0.35, 0xffb472, 2.6, 6.0),
  addPoint("L_StoreBack", 1.55, 2.05, -0.75, 0xffbb7a, 2.0, 5.0),
  addPoint("L_Checkout", 2.05, 1.55, 0.15, 0xffad68, 1.0, 3.1),
  addPoint("L_Canopy", 0.45, 2.20, 1.25, 0xffb96e, 0.6, 3.4),
  // Rear service elevation: keep the new backside readable from any orbit angle.
  addPoint("L_BackWash", 1.35, 2.10, -3.74, 0xffa968, 1.8, 4.8),
  addPoint("L_BackDoor", 2.72, 1.90, -3.66, 0xffc486, 0.75, 2.4),
  addPoint("L_BackCool", 0.10, 1.90, -3.62, 0x6ca9ff, 0.4, 2.5),
  addPoint("L_BackSign", 1.20, 3.30, -2.05, 0x9dffd8, 0.35, 2.5),
  addPoint("L_BackSide", -0.55, 1.55, -2.75, 0xffaa6f, 0.5, 2.4),
  addPoint("L_BackGate", -1.15, 1.30, -3.65, 0xffb06e, 0.55, 2.6),
  addPoint("L_BackServiceDoor", -2.80, 1.45, -3.68, 0xffbe82, 0.4, 2.4),
  addPoint("L_BackRight", 3.66, 2.0, -2.4, 0xffb377, 0.45, 2.4),
];
const neonLights = [
  addPoint("L_VendingCyan", -1.62, 1.10, 1.35, 0x68ddff, 1.0, 3.4),
  addPoint("L_VendingWarm", -1.18, 0.95, 1.32, 0xffaa78, 0.55, 2.5),
  addPoint("L_PinkNeon", 2.45, 1.90, 0.55, 0xff6f9f, 0.6, 3.2),
  addPoint("L_StreetLamp", -2.25, 2.75, 1.80, 0xffb86d, 2.4, 6.0),
  addPoint("L_BackNeon", 3.26, 2.05, -3.70, 0xff719e, 0.55, 2.7),
];
neonLights.forEach((l) => { l.userData.baseIntensity = l.intensity; });
const signLight = addPoint("L_SignFill", 1.55, 3.00, 0.70, 0xffd39c, 0.22, 4.2);
storeLights.forEach((l) => { l.userData.baseIntensity = l.intensity; });

/* ------------------------------------------------------------------------- */
/* Helpers                                                                    */
/* ------------------------------------------------------------------------- */
function smoothstep(a, b, x) {
  const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
}

function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function makeGradientMap() {
  const tones = [0.27, 0.52, 0.78, 1.0];
  const data = new Uint8Array(tones.length * 4);
  tones.forEach((v, i) => {
    const b = Math.round(v * 255);
    data[i * 4 + 0] = b;
    data[i * 4 + 1] = b;
    data[i * 4 + 2] = b;
    data[i * 4 + 3] = 255;
  });
  const tex = new THREE.DataTexture(data, tones.length, 1, THREE.RGBAFormat);
  tex.minFilter = THREE.NearestFilter;
  tex.magFilter = THREE.NearestFilter;
  tex.generateMipmaps = false;
  tex.needsUpdate = true;
  tex.colorSpace = THREE.NoColorSpace;
  return tex;
}
const gradientMap = makeGradientMap();

function makeRadialTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const ctx = c.getContext("2d");
  const g = ctx.createRadialGradient(128, 128, 0, 128, 128, 128);
  g.addColorStop(0, "rgba(255,255,255,0.95)");
  g.addColorStop(0.24, "rgba(255,255,255,0.55)");
  g.addColorStop(0.62, "rgba(255,255,255,0.12)");
  g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
const radialTexture = makeRadialTexture();

/* ------------------------------------------------------------------------- */
/* Scene load + material conversion                                           */
/* ------------------------------------------------------------------------- */
let gltfScene = null;
let composer = null;
let outlinePass = null;
let bloomPass = null;
let outlineObjects = [];
let signMesh = null;
let signBaseColor = null;
let signPoint = signLight;
let glowMaterials = [];
let doorRoots = [];
let traffic = [];
let glassRainPlanes = [];
let rainUniforms = null;
let rainGroup = null;
let splashGroup = null;
let glowGroup = null;
let modelLoadedAt = 0;
let activePreset = "hero";
let tween = null;
let neonOn = true;
let rainOn = true;
let spinOn = false;
let elapsed = 0;
let glbByteLength = 0;
const clock = new THREE.Clock();
const debugState = { fps: 0, meshes: 0, outlineCount: 0, frames: 0, last: 0 };

function inferKind(mesh, src) {
  const explicit = mesh.userData && mesh.userData.vx_kind;
  if (explicit) return explicit;
  const name = (src && src.name ? src.name : "").toLowerCase();
  if (name.includes("glass")) return "glass";
  if (name.includes("wet") || name.includes("puddle")) return "wet";
  if (name.includes("emit") || (src && src.emissiveIntensity > 0.2)) return "emissive";
  return "matte";
}

function createToonMaterial(src, kind) {
  const transparent = !!(src.transparent || src.opacity < 1);
  if (kind === "glass") {
    const m = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(0xbfe7f4),
      transparent: true,
      opacity: 0.13,
      roughness: 0.055,
      metalness: 0.0,
      clearcoat: 1.0,
      clearcoatRoughness: 0.04,
      envMapIntensity: 1.35,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    m.name = src.name + "_viewer_glass";
    m.userData.kind = "glass";
    return m;
  }
  if (kind === "wet") {
    const m = new THREE.MeshStandardMaterial({
      color: src.color ? src.color.clone() : new THREE.Color(0x151d27),
      roughness: Math.min(0.32, src.roughness ?? 0.2),
      metalness: Math.max(0.25, src.metalness ?? 0),
      envMapIntensity: 1.25,
      transparent,
      opacity: transparent ? src.opacity : 1,
    });
    m.name = src.name + "_viewer_wet";
    m.userData.kind = "wet";
    return m;
  }
  if (kind === "emissive") {
    const base = src.emissive && src.emissive.getHex() !== 0
      ? src.emissive.clone()
      : (src.color ? src.color.clone() : new THREE.Color(0xffffff));
    base.multiplyScalar(0.82 + Math.min(0.25, (src.emissiveIntensity || 1) * 0.04));
    const m = new THREE.MeshBasicMaterial({
      color: base,
      transparent,
      opacity: transparent ? Math.max(0.55, src.opacity) : 1,
      side: THREE.DoubleSide,
      toneMapped: true,
    });
    m.name = src.name + "_viewer_emissive";
    m.userData.kind = "emissive";
    m.userData.baseColor = base.clone();
    return m;
  }
  const m = new THREE.MeshToonMaterial({
    color: src.color ? src.color.clone() : new THREE.Color(0x9c9c9c),
    gradientMap,
    transparent,
    opacity: transparent ? src.opacity : 1,
    // Double-sided keeps small poster lettering and thin sign meshes readable
    // even when their normals face slightly away from the orbit camera.
    side: THREE.DoubleSide,
  });
  m.name = src.name + "_viewer_toon";
  m.userData.kind = "matte";
  return m;
}

function convertMaterials(root) {
  const cache = new Map();
  const emissiveByMesh = new Map();
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    const src = obj.material;
    if (!src) return;
    const srcList = Array.isArray(src) ? src : [src];
    const kind = inferKind(obj, srcList[0]);
    const out = srcList.map((m) => {
      const key = m.uuid + "|" + kind;
      if (!cache.has(key)) cache.set(key, createToonMaterial(m, kind));
      const converted = cache.get(key);
      if (kind === "emissive") {
        emissiveByMesh.set(obj, converted);
      }
      return converted;
    });
    obj.material = Array.isArray(src) ? out : out[0];
    obj.castShadow = obj.userData.vx_outline === true || obj.userData.vx_outline === 1;
    obj.receiveShadow = true;
    if (kind === "glass") {
      obj.castShadow = false;
      obj.receiveShadow = false;
      obj.renderOrder = 3;
    }
  });
  return emissiveByMesh;
}

function loadScene() {
  const bytes = glbBytes instanceof Uint8Array ? glbBytes : new Uint8Array(glbBytes);
  glbByteLength = bytes.byteLength;
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  const loader = new GLTFLoader();
  loader.parse(
    buffer,
    "",
    (gltf) => {
      try {
        onSceneLoaded(gltf);
      } catch (err) {
        console.error(err);
        showError("场景初始化出现错误：" + (err && err.message ? err.message : String(err)));
      }
    },
    (err) => {
      console.error(err);
      showError("无法解析内嵌的 3D 场景文件。");
    }
  );
}

function onSceneLoaded(gltf) {
  gltfScene = gltf.scene;
  scene.add(gltfScene);
  const emissiveByMesh = convertMaterials(gltfScene);

  // Outline selection
  outlineObjects = [];
  gltfScene.traverse((obj) => {
    if (!obj.isMesh) return;
    const flag = obj.userData && (obj.userData.vx_outline === true || obj.userData.vx_outline === 1);
    const kind = obj.userData && obj.userData.vx_kind;
    if (flag && kind !== "glass") outlineObjects.push(obj);
  });
  if (outlineObjects.length < 18) {
    // Safe fallback if a file is re-exported without extras.
    outlineObjects = [];
    gltfScene.traverse((obj) => {
      if (!obj.isMesh) return;
      if (obj.material && obj.material.userData && obj.material.userData.kind === "glass") return;
      obj.geometry.computeBoundingSphere();
      const r = obj.geometry.boundingSphere ? obj.geometry.boundingSphere.radius : 0;
      if (r > 0.22) outlineObjects.push(obj);
    });
  }
  outlineObjects = outlineObjects.slice(0, 420);

  // Find named nodes for animation.
  doorRoots = ["DOOR_L", "DOOR_R"]
    .map((name) => gltfScene.getObjectByName(name))
    .filter(Boolean)
    .map((root) => {
      const dir = new THREE.Vector3(1, 0, 0).applyQuaternion(root.quaternion).normalize();
      return {
        root,
        base: root.position.clone(),
        dir,
        sign: root.name.endsWith("_L") ? -1 : 1,
      };
    });

  // The optional A-frame reads well in the Blender still but crowds the window
  // in the interactive preset, so it is hidden only in the viewer.
  gltfScene.traverse((obj) => {
    if (obj.name && obj.name.startsWith("AFrame")) obj.visible = false;
  });

  signMesh = gltfScene.getObjectByName("Sign_LightFace");
  if (signMesh) {
    const m = Array.isArray(signMesh.material) ? signMesh.material[0] : signMesh.material;
    if (m && m.color) {
      m.userData.baseColor = m.color.clone();
      signBaseColor = m.userData.baseColor;
    }
  }

  traffic = ["TRAFFIC_RED", "TRAFFIC_AMBER", "TRAFFIC_GREEN"].map((name) => {
    const mesh = gltfScene.getObjectByName(name);
    if (!mesh) return null;
    const m = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
    if (!m || !m.color) return null;
    m.userData.baseColor = m.color.clone();
    return { mesh, material: m, color: m.color.clone() };
  }).filter(Boolean);

  // Soft light pools / wet reflections, recreated from the Blender art direction.
  buildLightPools();
  buildRain();
  buildGlassRain();

  // Post processing.
  const size = new THREE.Vector2();
  renderer.getDrawingBufferSize(size);
  const target = new THREE.WebGLRenderTarget(size.x, size.y, {
    type: THREE.HalfFloatType,
    samples: 4,
  });
  composer = new EffectComposer(renderer, target);
  const renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);
  outlinePass = new OutlinePass(new THREE.Vector2(size.x, size.y), scene, camera);
  outlinePass.selectedObjects = outlineObjects;
  outlinePass.edgeStrength = 2.5;
  outlinePass.edgeGlow = 0.0;
  outlinePass.edgeThickness = 1.05;
  outlinePass.visibleEdgeColor.set(0x08101a);
  outlinePass.hiddenEdgeColor.set(0x08101a);
  composer.addPass(outlinePass);
  bloomPass = new UnrealBloomPass(new THREE.Vector2(size.x, size.y), 0.18, 0.20, 1.15);
  composer.addPass(bloomPass);
  composer.addPass(new OutputPass());

  // Initialise UI from query parameters.
  const initialPreset = CAMERA_PRESETS[params.get("preset")] ? params.get("preset") : "hero";
  applyPreset(initialPreset, true);
  activePreset = initialPreset;
  if (hideUiAtStart) app.classList.add("ui-hidden");
  updateUiState();
  if (isDebug) debugEl.classList.add("is-on");

  debugState.meshes = 0;
  gltfScene.traverse((o) => { if (o.isMesh) debugState.meshes++; });
  debugState.outlineCount = outlineObjects.length;
  modelLoadedAt = performance.now();
  if (isDebug) {
    debugEl.textContent =
      `meshes ${debugState.meshes}\noutline ${outlineObjects.length}\n` +
      `glb ${(glbByteLength / 1048576).toFixed(1)} MB\nextras ${gltfScene.children[0]?.userData ? "yes" : "—"}`;
  }

  // Let the browser paint the first lit frame under the loading overlay.
  requestAnimationFrame(() => {
    renderer.render(scene, camera);
    setTimeout(() => loading.classList.add("is-done"), 380);
    window.__VIEWER_READY__ = true;
    document.documentElement.dataset.ready = "true";
    document.title = "雨夜のコンビニ | 星あかりマート";
  });
}

/* ------------------------------------------------------------------------- */
/* Wet light pools / neon reflections                                        */
/* ------------------------------------------------------------------------- */
function buildLightPools() {
  glowGroup = new THREE.Group();
  glowGroup.name = "WEB_LightPools";
  scene.add(glowGroup);
  const pools = [
    // x, z, width, depth, y, hex, opacity
    [1.20, 1.16, 4.0, 1.55, 0.185, 0xffa45d, 0.50],
    [-0.10, 1.20, 1.8, 1.0, 0.19, 0xffc273, 0.52],
    [-1.68, 1.42, 2.2, 1.25, 0.19, 0x64e3ff, 0.48],
    [-1.20, 1.40, 1.5, 0.9, 0.192, 0xff9461, 0.34],
    [-2.15, 1.85, 2.7, 2.0, 0.185, 0xffb769, 0.38],
    [3.12, 0.42, 1.2, 1.1, 0.19, 0xff9862, 0.32],
    // Road neon smears.
    [0.65, 2.20, 0.38, 2.0, 0.048, 0xffa257, 0.55],
    [1.65, 2.58, 0.26, 1.55, 0.049, 0xffcf86, 0.40],
    [-1.42, 2.58, 0.30, 1.35, 0.049, 0x61e4ff, 0.50],
    [2.38, 2.02, 0.22, 1.10, 0.049, 0xff6f9e, 0.46],
    [-2.18, 3.15, 0.18, 0.85, 0.048, 0xffae63, 0.36],
    // Rear service strip, only visible when the model is turned around.
    [1.35, -3.52, 2.9, 0.18, 0.19, 0xffa563, 0.42],
    [2.9, -3.52, 0.55, 0.16, 0.19, 0xff6f9b, 0.36],
    [0.15, -3.52, 0.55, 0.16, 0.19, 0x7cdcff, 0.30],
  ];
  for (const [x, z, w, d, y, color, opacity] of pools) {
    const material = new THREE.MeshBasicMaterial({
      map: radialTexture,
      color,
      transparent: true,
      opacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
      toneMapped: true,
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w, d), material);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(x, y, z);
    mesh.renderOrder = 2;
    mesh.userData.baseOpacity = opacity;
    glowGroup.add(mesh);
  }
  // A wider, gentler base wash avoids a dead black plinth in the vignette.
  const washMat = new THREE.MeshBasicMaterial({
    map: radialTexture,
    color: 0x244464,
    transparent: true,
    opacity: 0.18,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const wash = new THREE.Mesh(new THREE.PlaneGeometry(8.3, 8.3), washMat);
  wash.rotation.x = -Math.PI / 2;
  wash.position.set(0, 0.033, 0.25);
  wash.renderOrder = 1;
  glowGroup.add(wash);
}

/* ------------------------------------------------------------------------- */
/* Rain                                                                       */
/* ------------------------------------------------------------------------- */
function randomRainPosition(rand) {
  for (let attempt = 0; attempt < 30; attempt++) {
    const x = (rand() - 0.5) * 7.2;
    const z = (rand() - 0.5) * 7.2;
    // Keep rain out of the interior store volume.
    const insideStore = x > -0.45 && x < 2.75 && z > -1.95 && z < 0.85;
    if (!insideStore) return { x, z };
  }
  return { x: -3.0, z: 2.8 };
}

function buildRain() {
  rainGroup = new THREE.Group();
  rainGroup.name = "WEB_Rain";
  scene.add(rainGroup);

  const rand = mulberry32(23071);
  const isNarrow = window.innerWidth < 760;
  const count = isNarrow ? 580 : 1000;
  const positions = new Float32Array(count * 2 * 3);
  const phases = new Float32Array(count * 2);
  const speeds = new Float32Array(count * 2);
  const lengths = new Float32Array(count * 2);
  const ends = new Float32Array(count * 2);
  for (let i = 0; i < count; i++) {
    const { x, z } = randomRainPosition(rand);
    const phase = rand() * 6.4;
    const speed = 5.2 + rand() * 3.1;
    const len = 0.16 + rand() * 0.46;
    for (let k = 0; k < 2; k++) {
      const idx = i * 2 + k;
      positions[idx * 3 + 0] = x;
      positions[idx * 3 + 1] = 0;
      positions[idx * 3 + 2] = z;
      phases[idx] = phase;
      speeds[idx] = speed;
      lengths[idx] = len;
      ends[idx] = k;
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geo.setAttribute("aPhase", new THREE.BufferAttribute(phases, 1));
  geo.setAttribute("aSpeed", new THREE.BufferAttribute(speeds, 1));
  geo.setAttribute("aLen", new THREE.BufferAttribute(lengths, 1));
  geo.setAttribute("aEnd", new THREE.BufferAttribute(ends, 1));
  rainUniforms = {
    uTime: { value: 0 },
    uHeight: { value: 6.2 },
    uColor: { value: new THREE.Color(0xb9e6ff) },
    uOpacity: { value: 0.34 },
  };
  const rainMat = new THREE.ShaderMaterial({
    uniforms: rainUniforms,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    blending: THREE.AdditiveBlending,
    vertexShader: `
      attribute float aPhase;
      attribute float aSpeed;
      attribute float aLen;
      attribute float aEnd;
      uniform float uTime;
      uniform float uHeight;
      varying float vFade;
      void main() {
        float y = mod(aPhase - uTime * aSpeed, uHeight) - 0.25;
        vec3 p = position;
        p.y = y + aEnd * aLen;
        p.x += aEnd * 0.035;
        vFade = mix(0.38, 1.0, aEnd);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      uniform float uOpacity;
      varying float vFade;
      void main() {
        gl_FragColor = vec4(uColor, uOpacity * vFade);
      }
    `,
  });
  const rain = new THREE.LineSegments(geo, rainMat);
  rain.frustumCulled = false;
  rain.renderOrder = 7;
  rainGroup.add(rain);

  // Splash rings on the pavement.
  splashGroup = new THREE.Group();
  splashGroup.name = "WEB_Splashes";
  const ringGeo = new THREE.RingGeometry(0.84, 1.0, 30);
  for (let i = 0; i < 42; i++) {
    let x, z;
    let guard = 0;
    do {
      x = (rand() - 0.5) * 6.8;
      z = (rand() - 0.5) * 6.8;
      guard++;
    } while (x > -0.55 && x < 2.85 && z < 0.95 && z > -2.05 && guard < 40);
    const sidewalk = x > -2.0 && z < 2.0;
    const y = sidewalk ? 0.178 : 0.052;
    const material = new THREE.MeshBasicMaterial({
      color: i % 5 === 0 ? 0xffd39a : 0xbdefff,
      transparent: true,
      opacity: 0.2,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const ring = new THREE.Mesh(ringGeo, material);
    ring.rotation.x = -Math.PI / 2;
    ring.position.set(x, y, z);
    ring.userData.phase = rand();
    ring.userData.speed = 0.38 + rand() * 0.5;
    ring.userData.maxScale = 0.18 + rand() * 0.6;
    ring.userData.baseOpacity = 0.12 + rand() * 0.18;
    ring.renderOrder = 4;
    splashGroup.add(ring);
  }
  rainGroup.add(splashGroup);

  // Drips from the canopy edge, using simple additive beads.
  const dripGeo = new THREE.SphereGeometry(0.012, 6, 5);
  const dripMat = new THREE.MeshBasicMaterial({
    color: 0xc8f2ff,
    transparent: true,
    opacity: 0.52,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  for (let i = 0; i < 7; i++) {
    const drip = new THREE.Mesh(dripGeo, dripMat);
    drip.userData.x = -0.25 + i * 0.44;
    drip.userData.z = 1.09 + (i % 2) * 0.07;
    drip.userData.phase = rand();
    drip.userData.speed = 0.6 + rand() * 0.35;
    drip.position.set(drip.userData.x, 2.4, drip.userData.z);
    drip.renderOrder = 6;
    rainGroup.add(drip);
    drip.userData.kind = "drip";
  }
}

function buildGlassRain() {
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 512;
  const ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  const rand = mulberry32(9151);
  for (let i = 0; i < 115; i++) {
    const x = rand() * 256;
    const y = rand() * 512;
    const h = 8 + rand() * 65;
    const g = ctx.createLinearGradient(x, y, x, y + h);
    g.addColorStop(0, "rgba(220,248,255,0)");
    g.addColorStop(0.35, `rgba(222,247,255,${0.2 + rand() * 0.28})`);
    g.addColorStop(1, "rgba(200,238,255,0)");
    ctx.strokeStyle = g;
    ctx.lineWidth = 0.6 + rand() * 1.2;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + (rand() - 0.5) * 2.5, y + h);
    ctx.stroke();
  }
  for (let i = 0; i < 180; i++) {
    const x = rand() * 256;
    const y = rand() * 512;
    const r = 0.7 + rand() * 2.6;
    ctx.fillStyle = `rgba(225,249,255,${0.12 + rand() * 0.35})`;
    ctx.beginPath();
    ctx.ellipse(x, y, r, r * (1.1 + rand() * 1.4), 0, 0, Math.PI * 2);
    ctx.fill();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  const frontMat = new THREE.MeshBasicMaterial({
    map: tex,
    transparent: true,
    opacity: 0.48,
    depthWrite: false,
    blending: THREE.NormalBlending,
    side: THREE.DoubleSide,
  });
  const front = new THREE.Mesh(new THREE.PlaneGeometry(2.28, 2.22), frontMat);
  front.position.set(1.51, 1.33, 0.754);
  front.renderOrder = 5;
  rainGroup.add(front);
  glassRainPlanes.push({ mesh: front, offsetSpeed: 0.012, baseOpacity: 0.48 });

  const sideMat = frontMat.clone();
  sideMat.opacity = 0.34;
  const side = new THREE.Mesh(new THREE.PlaneGeometry(1.88, 2.22), sideMat);
  side.rotation.y = -Math.PI / 2;
  side.position.set(-0.362, 1.33, -0.92);
  side.renderOrder = 5;
  rainGroup.add(side);
  glassRainPlanes.push({ mesh: side, offsetSpeed: 0.009, baseOpacity: 0.34 });
}

/* ------------------------------------------------------------------------- */
/* Camera presets, UI, interaction                                           */
/* ------------------------------------------------------------------------- */
function setActiveViewButton(name) {
  document.querySelectorAll(".view-btn").forEach((b) => {
    b.classList.toggle("is-active", b.dataset.preset === name);
  });
}

function presetForViewport(name) {
  const preset = CAMERA_PRESETS[name] || CAMERA_PRESETS.hero;
  const portrait = window.innerWidth < 760 && window.innerHeight > window.innerWidth * 1.05;
  if (name === "hero" && portrait) {
    return {
      position: new THREE.Vector3(-4.35, 5.15, 14.2),
      target: new THREE.Vector3(0.58, 0.92, -0.10),
      fov: 43,
    };
  }
  return preset;
}

function startTween(preset) {
  const fromPos = camera.position.clone();
  const fromTarget = controls.target.clone();
  const fromFov = camera.fov;
  const to = presetForViewport(preset);
  tween = {
    start: performance.now(),
    duration: 1250,
    fromPos,
    fromTarget,
    fromFov,
    toPos: to.position.clone(),
    toTarget: to.target.clone(),
    toFov: to.fov,
  };
}

function applyPreset(name, instant = false) {
  if (!CAMERA_PRESETS[name]) name = "hero";
  activePreset = name;
  setActiveViewButton(name);
  const preset = presetForViewport(name);
  if (instant) {
    camera.position.copy(preset.position);
    controls.target.copy(preset.target);
    camera.fov = preset.fov;
    camera.updateProjectionMatrix();
    controls.update();
    tween = null;
  } else {
    startTween(name);
  }
}

function updateUiState() {
  document.querySelectorAll('[data-action="rain"]').forEach((b) =>
    b.classList.toggle("is-on", rainOn)
  );
  document.querySelectorAll('[data-action="neon"]').forEach((b) =>
    b.classList.toggle("is-on", neonOn)
  );
  document.querySelectorAll('[data-action="spin"]').forEach((b) =>
    b.classList.toggle("is-on", spinOn)
  );
}

function setRain(on) {
  rainOn = on;
  if (rainGroup) rainGroup.visible = on;
  updateUiState();
}

function setNeon(on) {
  neonOn = on;
  if (glowGroup) glowGroup.visible = on;
  if (bloomPass) bloomPass.strength = on ? 0.18 : 0.06;
  neonLights.forEach((l) => {
    l.intensity = on ? l.userData.baseIntensity : 0;
  });
  updateUiState();
}

function setSpin(on) {
  spinOn = on;
  controls.autoRotate = on;
  updateUiState();
}

function resetView() {
  setRain(true);
  setSpin(false);
  setNeon(true);
  app.classList.remove("ui-hidden");
  applyPreset("hero", false);
  if (hintEl) hintEl.classList.remove("is-gone");
}

document.querySelectorAll(".view-btn").forEach((button) => {
  button.addEventListener("click", () => applyPreset(button.dataset.preset));
});
document.querySelectorAll(".tool-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const action = button.dataset.action;
    if (action === "rain") setRain(!rainOn);
    else if (action === "neon") setNeon(!neonOn);
    else if (action === "spin") setSpin(!spinOn);
    else if (action === "reset") resetView();
  });
});
document.getElementById("hideUi").addEventListener("click", () => app.classList.add("ui-hidden"));
document.getElementById("showUi").addEventListener("click", () => app.classList.remove("ui-hidden"));

canvas.addEventListener("pointerdown", () => {
  if (hintEl) hintEl.classList.add("is-gone");
});
controls.addEventListener("start", () => { tween = null; });

window.addEventListener("keydown", (event) => {
  if (event.target && /input|textarea|select/i.test(event.target.tagName)) return;
  const key = event.key.toLowerCase();
  if (key === "h") app.classList.toggle("ui-hidden");
  else if (key === "r") resetView();
  else if (key === " ") {
    event.preventDefault();
    setSpin(!spinOn);
  } else if (key === "1") applyPreset("hero");
  else if (key === "2") applyPreset("street");
  else if (key === "3") applyPreset("interior");
  else if (key === "4") applyPreset("top");
  else if (key === "5") applyPreset("back");
});

window.addEventListener("resize", () => {
  const w = window.innerWidth;
  const h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h, false);
  if (composer) composer.setSize(w, h);
});

window.addEventListener("error", (event) => {
  if (!window.__VIEWER_READY__) {
    console.error(event.error || event.message);
  }
});

/* ------------------------------------------------------------------------- */
/* Animation                                                                 */
/* ------------------------------------------------------------------------- */
function animateDoors(time) {
  const period = 18.0;
  const t = (time + 2.0) % period;
  let open = 0;
  if (t < 2.4) open = smoothstep(0, 2.4, t);
  else if (t < 6.0) open = 1;
  else if (t < 8.4) open = 1 - smoothstep(6.0, 8.4, t);
  const amount = open * 0.44;
  for (const door of doorRoots) {
    door.root.position.copy(door.base).addScaledVector(door.dir, door.sign * amount);
  }
}

function animateTraffic(time) {
  if (!traffic.length) return;
  const cycle = (time + 3.0) % 22.0;
  let active = "green";
  if (cycle > 8.5 && cycle <= 10.5) active = "amber";
  else if (cycle > 10.5 && cycle <= 21.0) active = "red";
  for (const lamp of traffic) {
    const target = lamp.mesh.name.includes(active.toUpperCase()) ? 1.75 : 0.035;
    lamp.material.color.copy(lamp.color).multiplyScalar(target);
  }
}

function animateSign(time) {
  if (!signMesh || !signBaseColor) return;
  const m = Array.isArray(signMesh.material) ? signMesh.material[0] : signMesh.material;
  if (!m || !m.color) return;
  let flicker = 1.0;
  const micro = Math.sin(time * 2.1) * 0.025 + Math.sin(time * 7.7) * 0.012;
  if ((time % 19.0) > 18.55) flicker = 0.55;
  else if ((time % 31.0) > 30.7) flicker = 0.75;
  const value = Math.max(0.4, 1.0 + micro) * flicker;
  m.color.copy(signBaseColor).multiplyScalar(value);
  if (signPoint) signPoint.intensity = 0.22 * value;
}

function animateSplashes(time) {
  if (!splashGroup) return;
  for (const ring of splashGroup.children) {
    const phase = (time * ring.userData.speed + ring.userData.phase) % 1;
    const scale = 0.06 + phase * ring.userData.maxScale;
    ring.scale.setScalar(scale);
    ring.material.opacity = (1 - phase) * ring.userData.baseOpacity;
  }
  for (const child of rainGroup.children) {
    if (child.userData.kind !== "drip") continue;
    const phase = (time * child.userData.speed + child.userData.phase) % 1;
    child.position.y = 2.4 - phase * 2.12;
    child.position.x = child.userData.x + Math.sin(phase * 4.0) * 0.01;
    child.scale.setScalar(phase > 0.93 ? 0.6 : 1.0);
  }
}

function updateTween(now) {
  if (!tween) return;
  const p = Math.min(1, (now - tween.start) / tween.duration);
  const e = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
  camera.position.lerpVectors(tween.fromPos, tween.toPos, e);
  controls.target.lerpVectors(tween.fromTarget, tween.toTarget, e);
  camera.fov = tween.fromFov + (tween.toFov - tween.fromFov) * e;
  camera.updateProjectionMatrix();
  if (p >= 1) tween = null;
}

function updateGlowGroup(time) {
  if (!glowGroup) return;
  glowGroup.children.forEach((mesh, i) => {
    if (!mesh.material || !mesh.material.opacity) return;
    if (i < 11) {
      mesh.material.opacity = mesh.userData.baseOpacity * (0.96 + Math.sin(time * 1.7 + i * 1.2) * 0.04);
    }
  });
}

let debugTimer = 0;
function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(0.05, clock.getDelta());
  elapsed += dt;

  if (rainUniforms) rainUniforms.uTime.value = elapsed;
  if (glassRainPlanes.length) {
    glassRainPlanes.forEach((entry, i) => {
      const map = entry.mesh.material.map;
      if (map) map.offset.y = -((elapsed * entry.offsetSpeed) % 1);
      entry.mesh.material.opacity = entry.baseOpacity * (0.9 + Math.sin(elapsed * 0.8 + i) * 0.08);
    });
  }
  animateDoors(elapsed);
  animateTraffic(elapsed);
  animateSign(elapsed);
  animateSplashes(elapsed);
  updateGlowGroup(elapsed);
  updateTween(performance.now());
  controls.update();
  if (composer) {
    composer.render();
  } else {
    renderer.render(scene, camera);
  }

  debugState.frames++;
  debugTimer += dt;
  if (debugTimer > 0.5) {
    debugState.fps = Math.round(debugState.frames / debugTimer);
    debugState.frames = 0;
    debugTimer = 0;
    if (debugEl && isDebug) {
      debugEl.textContent =
        `meshes ${debugState.meshes}\noutline ${debugState.outlineCount}\n` +
        `fps ${debugState.fps}\nrain ${rainOn ? "on" : "off"} / neon ${neonOn ? "on" : "off"}`;
    }
  }
}

// Apply requested initial state, then start loading + render loop.
if (hideUiAtStart) app.classList.add("ui-hidden");
loadScene();
animate();
