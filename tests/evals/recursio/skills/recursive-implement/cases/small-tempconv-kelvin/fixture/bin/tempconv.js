#!/usr/bin/env node
// @ts-check
// The tempconv command.
import { run } from '../src/cli.js';

const result = run(process.argv.slice(2));
process.stdout.write(result.output);
process.stderr.write(result.error);
process.exitCode = result.status;
