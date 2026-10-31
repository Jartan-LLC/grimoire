// SPDX-License-Identifier: MIT
// The wordfreq command, kept free of process state so tests can run it.
import { countWords, top } from './wordfreq.js';

const USAGE = 'usage: wordfreq FILE [--top N] [--min-count N]';

function usage(message) {
  return { status: 2, output: '', error: message ? `wordfreq: ${message}\n${USAGE}\n` : `${USAGE}\n` };
}

export function run(argv, readText) {
  let file;
  let limit = Infinity;
  let minCount = 1;
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--top' || argv[i] === '--min-count') {
      const value = Number(argv[i + 1]);
      if (!Number.isInteger(value) || value < 1) return usage(`${argv[i]} needs a positive whole number`);
      if (argv[i] === '--top') limit = value;
      else minCount = value;
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
  const kept = top(countWords(text)).filter(([, count]) => count >= minCount).slice(0, limit);
  return { status: 0, output: kept.map(([word, count]) => `${count} ${word}\n`).join(''), error: '' };
}
