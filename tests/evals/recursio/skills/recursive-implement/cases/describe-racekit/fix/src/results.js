// Reading the chip times.
import { RaceError, parseClock } from './clock.js';

/**
 * The race's rows.
 * @param {string} text - the CSV, header first.
 * @returns {{bib: number, name: string, born: number, sex: string, seconds: number | null}[]} the rows in file order.
 */
export function parseResults(text) {
  const results = [];
  const bibs = new Set();
  text.split('\n').forEach((line, i) => {
    if (i === 0 || line.trim() === '') return;
    const fail = (why) => {
      throw new RaceError(`line ${i + 1}: ${why}`);
    };
    const fields = line.split(',');
    if (fields.length !== 6) fail(`expected 6 fields, got ${fields.length}`);
    const [bibText, name, bornText, sex, start, finish] = fields.map((f) => f.trim());
    if (!/^\d+$/.test(bibText)) fail(`bad bib ${bibText}`);
    if (!/^\d{4}$/.test(bornText)) fail(`bad year ${bornText}`);
    if (sex !== 'F' && sex !== 'M') fail(`bad sex ${sex}`);
    const bib = Number(bibText);
    if (bibs.has(bib)) fail(`bib ${bib} used twice`);
    bibs.add(bib);
    let seconds = null;
    try {
      const from = parseClock(start);
      if (finish !== '') seconds = parseClock(finish) - from;
    } catch (error) {
      fail(error.message);
    }
    if (seconds !== null && seconds <= 0) fail('finish is not after start');
    results.push({ bib, name, born: Number(bornText), sex, seconds });
  });
  return results;
}

/**
 * The runners who finished.
 * @param {{seconds: number | null}[]} results - rows from parseResults.
 * @returns {object[]} the finishers, fastest first, the same time in file order.
 */
export function finishers(results) {
  return results.filter((r) => r.seconds !== null).sort((a, b) => a.seconds - b.seconds);
}
