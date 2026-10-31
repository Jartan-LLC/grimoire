#!/usr/bin/env node
// SPDX-License-Identifier: ISC
import { readFileSync } from 'node:fs';
import { run } from '../src/cli.js';

const result = run(process.argv.slice(2), (path) => readFileSync(path, 'utf8'));
process.stdout.write(result.output);
process.stderr.write(result.error);
process.exitCode = result.status;
