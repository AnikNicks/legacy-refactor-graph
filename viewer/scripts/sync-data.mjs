// Snapshot output/**/*.json + output/**/*.md into public/data/ (mirroring
// the output/<target>/ structure) for a static `npm run build` (e.g. GitHub
// Pages). Not used by `npm run dev` — the dev server reads output/ live (see
// vite.config.ts's liveOutputData plugin) so it never goes stale.
// See sync-source.mjs for the companion script that does the same for the
// source-viewer panel's data.
import { copyFileSync, existsSync, mkdirSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outputDir = join(__dirname, "..", "..", "output");
const targetDir = join(__dirname, "..", "public", "data");

mkdirSync(targetDir, { recursive: true });

if (!existsSync(outputDir)) {
  console.log(`sync-data: no output/ directory yet at ${outputDir}, nothing to copy`);
  process.exit(0);
}

function copyRecursive(srcDir, destDir) {
  let count = 0;
  mkdirSync(destDir, { recursive: true });
  for (const entry of readdirSync(srcDir)) {
    const srcPath = join(srcDir, entry);
    if (statSync(srcPath).isDirectory()) {
      count += copyRecursive(srcPath, join(destDir, entry));
    } else if (entry.endsWith(".json") || entry.endsWith(".md")) {
      copyFileSync(srcPath, join(destDir, entry));
      count += 1;
    }
  }
  return count;
}

const count = copyRecursive(outputDir, targetDir);
console.log(`sync-data: copied ${count} file(s) from output/ to public/data/`);
