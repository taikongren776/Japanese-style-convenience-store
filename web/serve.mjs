import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const dist = path.resolve(here, "..", "dist");
const preferredPort = Number(process.env.PORT || 5188);
const viewerName = "hoshiakari-mart-rainy-night.html";
const mime = {
  ".html": "text/html; charset=utf-8",
  ".glb": "model/gltf-binary",
  ".png": "image/png",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

function serve(port) {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url || "/", `http://127.0.0.1:${port}`);
    let pathname = decodeURIComponent(url.pathname);
    if (pathname === "/" || pathname === "/viewer" || pathname === "/viewer.html") {
      pathname = "/" + viewerName;
    }
    const target = path.normalize(path.join(dist, pathname));
    if (!target.startsWith(dist) || !fs.existsSync(target) || !fs.statSync(target).isFile()) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Not found");
      return;
    }
    const ext = path.extname(target).toLowerCase();
    res.writeHead(200, {
      "Content-Type": mime[ext] || "application/octet-stream",
      "Cache-Control": "no-cache",
      "Cross-Origin-Resource-Policy": "same-origin",
    });
    fs.createReadStream(target).pipe(res);
  });
  server.on("error", (err) => {
    if (err.code === "EADDRINUSE" && port < preferredPort + 10) {
      serve(port + 1);
    } else {
      console.error("SERVER_ERROR", err);
      process.exit(1);
    }
  });
  server.listen(port, "127.0.0.1", () => {
    console.log(`VIEWER_URL=http://127.0.0.1:${port}/`);
    console.log(`VIEWER_FILE=${path.join(dist, viewerName)}`);
  });
}

serve(preferredPort);
