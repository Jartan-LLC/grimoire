/** Project lint: every export in a TypeScript file has a doc comment right above it. */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const EXPORT = /^export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|type|interface)\b/;

/** Every .ts file under `dir`, sorted. */
export function files(dir: string): string[] {
  let names: string[] = [];
  try {
    names = readdirSync(dir);
  } catch {
    return [];
  }
  return names.sort().flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return files(path);
    return path.endsWith('.ts') ? [path] : [];
  });
}

const bad: string[] = [];
for (const path of ['src', 'bin', 'test', 'scripts'].flatMap(files)) {
  const lines = readFileSync(path, 'utf8').split('\n');
  lines.forEach((line, i) => {
    if (!EXPORT.test(line)) return;
    const above = lines.slice(0, i).filter((l) => l.trim() !== '').at(-1) ?? '';
    if (!above.trim().endsWith('*/')) bad.push(`${path}:${i + 1}: an export needs a /** ... */ comment right above it`);
  });
}
for (const message of bad) console.log(message);
process.exitCode = bad.length ? 1 : 0;
