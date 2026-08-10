import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..");
const outputDir = join(repoRoot, "output");

const SOURCE_EXTENSIONS = new Set([".py", ".txt", ".md", ".json", ".cfg", ".toml"]);
const SOURCE_SKIP_DIRS = new Set(["__pycache__", "node_modules", ".git", "tests"]);

// Only serves files that resolve inside `base` — guards both source-serving
// routes below against a `..` segment escaping the intended app directory.
function safeJoin(base: string, ...segments: string[]): string | null {
  const target = resolve(base, ...segments);
  if (target !== base && !target.startsWith(base + sep)) {
    return null;
  }
  return target;
}

function listSourceFiles(dir: string, base: string, acc: string[] = []): string[] {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".")) continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (SOURCE_SKIP_DIRS.has(entry.name)) continue;
      listSourceFiles(full, base, acc);
    } else if (SOURCE_EXTENSIONS.has(entry.name.slice(entry.name.lastIndexOf(".")))) {
      acc.push(relative(base, full).split(sep).join("/"));
    }
  }
  return acc;
}

// Serves /data/<target>/<file> and /data/examples.json straight from the
// pipeline's own output/ directory, read fresh on every request — so the
// dashboard reflects whatever the orchestrator just wrote without any
// copy/sync step or rebuild. Dev only; `npm run build` uses
// scripts/sync-data.mjs to snapshot output/ once since a static build (e.g.
// GitHub Pages) has no server to read from live.
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
        const filePath = safeJoin(outputDir, file);
        if (!filePath || !existsSync(filePath)) {
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

// Serves the actual source of each example target, read live from the repo
// root, at the same URL shape scripts/sync-source.mjs produces as static
// files for a production build:
//   /source-data/<target>/__index__.json  → JSON array of relative file paths
//   /source-data/<target>/<path>          → one file's raw text
// Using one identical shape for both means SourceViewerPanel never has to
// know whether it's talking to this live dev middleware or to static files
// on GitHub Pages.
function sourceServer(): Plugin {
  return {
    name: "source-server",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url ?? "";
        if (!url.startsWith("/source-data/")) {
          next();
          return;
        }

        const rest = decodeURIComponent(url.replace("/source-data/", "").split("?")[0]);
        const slashIdx = rest.indexOf("/");
        const target = slashIdx === -1 ? rest : rest.slice(0, slashIdx);
        const relPath = slashIdx === -1 ? "" : rest.slice(slashIdx + 1);
        const targetDir = safeJoin(repoRoot, target);

        if (relPath === "__index__.json") {
          if (!targetDir || !existsSync(targetDir) || !statSync(targetDir).isDirectory()) {
            res.statusCode = 404;
            res.end("[]");
            return;
          }
          const files = listSourceFiles(targetDir, targetDir).sort();
          res.setHeader("Content-Type", "application/json");
          res.setHeader("Cache-Control", "no-store");
          res.end(JSON.stringify(files));
          return;
        }

        const filePath = targetDir ? safeJoin(targetDir, relPath) : null;
        if (!filePath || !existsSync(filePath)) {
          res.statusCode = 404;
          res.end("not found");
          return;
        }
        res.setHeader("Content-Type", "text/plain; charset=utf-8");
        res.setHeader("Cache-Control", "no-store");
        res.end(readFileSync(filePath));
      });
    },
  };
}

export default defineConfig(({ mode }) => ({
  // GitHub Pages serves a project site under /<repo-name>/, not the domain
  // root — the dev server always serves at root regardless of this value,
  // so it's conditional on build mode rather than needing base-aware
  // middleware matching above.
  base: mode === "production" ? "/legacy-refactor-graph/" : "/",
  plugins: [react(), liveOutputData(), sourceServer()],
}));
