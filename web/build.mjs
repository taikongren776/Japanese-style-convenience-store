import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const dist = path.join(root, "dist");
const bundlePath = path.join(dist, "_viewer.bundle.js");
const templateUrl = new URL("./index.template.html", import.meta.url);
const mainPath = path.join(here, "src", "main.js");
const cssPath = path.join(here, "style.css");
const outPath = path.join(dist, "hoshiakari-mart-rainy-night.html");

fs.mkdirSync(dist, { recursive: true });

const platformArch = `${process.platform}-${process.arch}`;
const candidates = [
  path.join(root, "node_modules", "@esbuild", platformArch, process.platform === "win32" ? "esbuild.exe" : "bin/esbuild"),
  path.join(root, "node_modules", "@esbuild", "win32-x64", "esbuild.exe"),
];
const esbuild = candidates.find((p) => fs.existsSync(p));
if (!esbuild) {
  console.error("esbuild binary not found. Run npm install.");
  process.exit(1);
}

console.log("Bundling viewer with", esbuild);
const result = spawnSync(
  esbuild,
  [
    mainPath,
    "--bundle",
    "--format=iife",
    "--minify",
    "--charset=utf8",
    "--legal-comments=none",
    "--target=es2019",
    "--loader:.glb=binary",
    "--define:process.env.NODE_ENV=\"production\"",
    `--outfile=${bundlePath}`,
  ],
  { cwd: root, encoding: "utf8" }
);
if (result.status !== 0) {
  console.error(result.stdout || "");
  console.error(result.stderr || "esbuild failed");
  process.exit(result.status || 1);
}

const bundle = fs.readFileSync(bundlePath, "utf8");
const css = fs.readFileSync(cssPath, "utf8");
let html = fs.readFileSync(templateUrl, "utf8");
const safeJs = bundle.replace(/<\/script>/gi, "<\\/script>");
html = html.replace("/*__CSS__*/", () => css);
html = html.replace("/*__JS__*/", () => safeJs);
fs.writeFileSync(outPath, html);
fs.unlinkSync(bundlePath);

const mb = (n) => (n / 1048576).toFixed(2) + " MB";
console.log("VIEWER_HTML", outPath, mb(fs.statSync(outPath).size));
console.log("SCENE_GLB", path.join(dist, "scene.glb"), mb(fs.statSync(path.join(dist, "scene.glb")).size));
