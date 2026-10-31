// Project lint: every exported function in src/ and bin/ has a JSDoc comment right above it with a @returns tag.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const EXPORT = /^export\s+(?:default\s+)?(?:async\s+)?function\b|^export\s+const\s+\w+\s*=\s*(?:async\s+)?(?:function\b|\(|\w+\s*=>)/;

function files(dir) {
  let names = [];
  try {
    names = readdirSync(dir);
  } catch {
    return [];
  }
  return names.sort().flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return files(path);
    return path.endsWith('.js') ? [path] : [];
  });
}

const bad = [];
for (const path of ['src', 'bin'].flatMap(files)) {
  const lines = readFileSync(path, 'utf8').split('\n');
  lines.forEach((line, i) => {
    if (!EXPORT.test(line)) return;
    const above = lines.slice(0, i).join('\n').trimEnd();
    const doc = above.endsWith('*/') ? above.slice(above.lastIndexOf('/**')) : '';
    if (!/@returns?\b/.test(doc)) bad.push(`${path}:${i + 1}: an exported function needs a /** ... */ comment right above it with @returns`);
  });
}
for (const message of bad) console.log(message);
process.exitCode = bad.length ? 1 : 0;
