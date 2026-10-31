// Project lint: every exported function in src/ declares its return type.
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

const START = /^export\s+(?:default\s+)?(?:async\s+)?function\b|^export\s+const\s+\w+\s*=\s*(?:async\s+)?\(/;

/** Whether the parameter list that opens at or after `from` is followed by `: ReturnType`. */
function declaresReturn(text: string, from: number): boolean {
  let depth = 0;
  for (let i = text.indexOf('(', from); i >= 0 && i < text.length; i += 1) {
    if (text[i] === '(') depth += 1;
    if (text[i] === ')' && --depth === 0) return /^\s*:/.test(text.slice(i + 1));
  }
  return false;
}

const bad: string[] = [];
for (const path of files('src')) {
  const text = readFileSync(path, 'utf8');
  text.split('\n').forEach((line, i, lines) => {
    if (!START.test(line)) return;
    const offset = lines.slice(0, i).reduce((sum, l) => sum + l.length + 1, 0);
    if (!declaresReturn(text, offset)) bad.push(`${path}:${i + 1}: an exported function must declare its return type`);
  });
}
for (const message of bad) console.log(message);
process.exitCode = bad.length ? 1 : 0;
