#!/usr/bin/env node
// The pantrykit command, wired to the file system and the process.
import { readFileSync, writeFileSync } from 'node:fs';
import { run } from '../src/cli.ts';

const result = run(process.argv.slice(2), {
  read: (path) => readFileSync(path, 'utf8'),
  write: (path, text) => writeFileSync(path, text),
});
process.stdout.write(result.output);
process.stderr.write(result.error);
process.exitCode = result.status;
