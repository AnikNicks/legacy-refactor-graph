// Snapshot each example target's actual source into public/source-data/,
// at the same shape vite.config.ts's dev-only sourceServer middleware
// serves live: public/source-data/<target>/__index__.json (a JSON array of
// relative file paths) plus a copy of every one of those files. Needed for
// SourceViewerPanel to work on a static `npm run build` (e.g. GitHub Pages)
// — see sync-data.mjs for the companion script that does the same for the
// data panels.
import { copyFileSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..");
const outputDir = join(repoRoot, "output");
const targetDir = join(__dirname, "..", "public", "source-data");

const SOURCE_EXTENSIONS = new Set([".py", ".txt", ".md", ".json", ".cfg", ".toml"]);
const SOURCE_SKIP_DIRS = new Set(["__pycache__", "node_modules", ".git", "tests"]);

function listSourceFiles(dir, base, acc = []) {
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

const examplesPath = join(outputDir, "examples.json");
let slugs = [];
try {
  const manifest = JSON.parse(readFileSync(examplesPath, "utf-8"));
  slugs = manifest.examples.map((e) => e.appPath);
} catch {
  console.log(`sync-source: no output/examples.json at ${examplesPath}, nothing to copy`);
  process.exit(0);
}

let fileCount = 0;
for (const slug of slugs) {
  const srcDir = join(repoRoot, slug);
  if (!statSync(srcDir, { throwIfNoEntry: false })?.isDirectory()) continue;

  const files = listSourceFiles(srcDir, srcDir).sort();
  const destDir = join(targetDir, slug);
  mkdirSync(destDir, { recursive: true });
  writeFileSync(join(destDir, "__index__.json"), JSON.stringify(files));

  for (const file of files) {
    const destFile = join(destDir, ...file.split("/"));
    mkdirSync(dirname(destFile), { recursive: true });
    copyFileSync(join(srcDir, ...file.split("/")), destFile);
    fileCount += 1;
  }
}

console.log(`sync-source: copied ${fileCount} source file(s) across ${slugs.length} target(s) into public/source-data/`);
