import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outputDir = join(__dirname, "..", "output");

// Serves /data/<file> straight from the pipeline's own output/ directory,
// read fresh on every request — so the dashboard reflects whatever the
// orchestrator just wrote without any copy/sync step or rebuild. Dev only;
// `npm run build` uses scripts/sync-data.mjs to snapshot output/ once since
// a static build has no server to read from live.
function liveOutputData(): Plugin {
  return {
    name: "live-output-data",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!req.url?.startsWith("/data/")) {
          next();
          return;
        }
        const file = req.url.replace("/data/", "").split("?")[0];
        const filePath = join(outputDir, file);
        if (!existsSync(filePath)) {
          res.statusCode = 404;
          res.end("not found");
          return;
        }
        res.setHeader(
          "Content-Type",
          file.endsWith(".json") ? "application/json" : "text/plain",
        );
        res.setHeader("Cache-Control", "no-store");
        res.end(readFileSync(filePath));
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), liveOutputData()],
});
