#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { run } from '../src/cli.ts';

const result = run(process.argv.slice(2), (path) => readFileSync(path, 'utf8'));
process.stdout.write(result.output);
process.stderr.write(result.error);
process.exitCode = result.status;
