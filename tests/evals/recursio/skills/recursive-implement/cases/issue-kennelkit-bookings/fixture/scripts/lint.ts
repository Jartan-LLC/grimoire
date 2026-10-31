/** @file Project lint: every TypeScript file opens with a doc comment that has a @file tag. */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

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

const bad = ['src', 'bin', 'test', 'scripts'].flatMap(files).filter((path) => {
  const text = readFileSync(path, 'utf8').replace(/^#!.*\n/, '').trimStart();
  return !(text.startsWith('/**') && text.slice(0, text.indexOf('*/')).includes('@file'));
});
for (const path of bad) console.log(`${path}: must open with a /** @file ... */ comment`);
process.exitCode = bad.length ? 1 : 0;
