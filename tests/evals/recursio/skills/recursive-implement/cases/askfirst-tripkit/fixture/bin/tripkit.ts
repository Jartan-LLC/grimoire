#!/usr/bin/env node
// Copyright 2026 tripkit contributors. MIT licence.
import { readFileSync } from 'node:fs';
import { run } from '../src/cli.ts';

const result = await run(process.argv.slice(2), (path) => readFileSync(path, 'utf8'));
process.stdout.write(result.output);
process.stderr.write(result.error);
process.exitCode = result.status;
