#!/usr/bin/env node
// SPDX-License-Identifier: BSD-3-Clause
import { run } from '../src/cli.ts';

const result = run(process.argv.slice(2));
process.stdout.write(result.output);
process.stderr.write(result.error);
process.exitCode = result.status;
