// Snapshot output/*.json + output/*.md into public/data/ for a static
// `npm run build`. Not used by `npm run dev` — the dev server reads output/
// live (see vite.config.ts's liveOutputData plugin) so it never goes stale.
import { copyFileSync, existsSync, mkdirSync, readdirSync } from "node:fs";
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

const files = readdirSync(outputDir).filter(
  (f) => f.endsWith(".json") || f.endsWith(".md"),
);
for (const f of files) {
  copyFileSync(join(outputDir, f), join(targetDir, f));
}
console.log(`sync-data: copied ${files.length} file(s) from output/ to public/data/`);
