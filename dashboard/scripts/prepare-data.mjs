/**
 * Copy the committed artefacts the dashboard reads into `dashboard/data/`.
 *
 * The dashboard has no database and no API: it reads the deployment record, the agent's
 * ledger, the chain-verified cycle record and the backtest metrics from the repository.
 * In a local checkout those files are one directory up. A hosted deployment only gets
 * the dashboard's own directory, so this script copies the same files in before the
 * build, and `src/lib/deployment.ts` looks there first.
 *
 * The copies are build output and are not committed. The source of truth stays in the
 * repository, one copy per file.
 */
import { copyFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(appRoot, "..");
const outDir = path.join(appRoot, "data");
const publicDir = path.join(appRoot, "public");

const files = [
  ["deployments/base-sepolia.json", "base-sepolia.json"],
  ["agent/ledger/cycles.jsonl", "cycles.jsonl"],
  ["agent/ledger/chain-events.jsonl", "chain-events.jsonl"],
  ["agent/models/metrics.json", "metrics.json"],
  ["docs/BENCHMARK.md", "BENCHMARK.md"],
];

await mkdir(outDir, { recursive: true });

for (const [from, to] of files) {
  const source = path.join(repoRoot, from);
  const target = path.join(outDir, to);
  try {
    await copyFile(source, target);
    console.log(`copied ${from} -> data/${to}`);
  } catch (error) {
    // A missing optional file must not fail the build: the dashboard shows an empty
    // state for it and says so on the page.
    console.warn(`skipped ${from}: ${error.message}`);
  }
}

// The demo video is committed once, at `docs/helm-demo.mp4`. The hosted build copies it
// into `public/` so the submission can link to a stable URL instead of to a raw file
// host. The copy is build output; the committed file is the source of truth.
await mkdir(publicDir, { recursive: true });
try {
  await copyFile(
    path.join(repoRoot, "docs", "helm-demo.mp4"),
    path.join(publicDir, "helm-demo.mp4"),
  );
  console.log("copied docs/helm-demo.mp4 -> public/helm-demo.mp4");
} catch (error) {
  console.warn(`skipped docs/helm-demo.mp4: ${error.message}`);
}
