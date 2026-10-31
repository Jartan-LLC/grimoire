// SPDX-License-Identifier: BSD-3-Clause
// Project lint: every TypeScript file starts with the SPDX line, after any #! line.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const LINE = '// SPDX-License-Identifier: BSD-3-Clause';

function files(dir: string): string[] {
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

const bad = ['src', 'bin', 'test', 'scripts']
  .flatMap(files)
  .filter((path) => !readFileSync(path, 'utf8').replace(/^#!.*\n/, '').startsWith(`${LINE}\n`));
for (const path of bad) console.log(`${path}: the first line must be '${LINE}'`);
process.exitCode = bad.length ? 1 : 0;
