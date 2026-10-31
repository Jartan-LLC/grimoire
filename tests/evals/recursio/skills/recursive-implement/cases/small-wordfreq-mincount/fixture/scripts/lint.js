// SPDX-License-Identifier: MIT
// Project lint: every JavaScript file starts with the SPDX line, after any #! line.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const LINE = '// SPDX-License-Identifier: MIT';

function files(dir) {
  let found = [];
  let names = [];
  try {
    names = readdirSync(dir);
  } catch {
    return found;
  }
  for (const name of names.sort()) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) found = found.concat(files(path));
    else if (path.endsWith('.js')) found.push(path);
  }
  return found;
}

const bad = ['src', 'bin', 'test', 'scripts']
  .flatMap(files)
  .filter((path) => !readFileSync(path, 'utf8').replace(/^#!.*\n/, '').startsWith(`${LINE}\n`));
for (const path of bad) console.log(`${path}: the first line must be '${LINE}'`);
process.exitCode = bad.length ? 1 : 0;
