// SPDX-License-Identifier: MIT
// The wordfreq command, kept free of process state so tests can run it.
import { countWords, top } from './wordfreq.js';

const USAGE = 'usage: wordfreq FILE [--top N]';

function usage(message) {
  return { status: 2, output: '', error: message ? `wordfreq: ${message}\n${USAGE}\n` : `${USAGE}\n` };
}

export function run(argv, readText) {
  let file;
  let limit = Infinity;
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--top') {
      limit = Number(argv[i + 1]);
      if (!Number.isInteger(limit) || limit < 1) return usage('--top needs a positive whole number');
      i += 1;
    } else if (file === undefined) {
      file = argv[i];
    } else {
      return usage();
    }
  }
  if (file === undefined) return usage();
  let text;
  try {
    text = readText(file);
  } catch {
    return { status: 2, output: '', error: `wordfreq: cannot read ${file}\n` };
  }
  const lines = top(countWords(text), limit).map(([word, count]) => `${count} ${word}\n`);
  return { status: 0, output: lines.join(''), error: '' };
}
