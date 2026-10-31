// Pieces the other modules share: the error type and clock arithmetic.

/** Bad input: a row, a time or a command line that cannot be used. */
export class RaceError extends Error {}

/**
 * A time of day as seconds since midnight.
 * @param {string} text - the time, as `HH:MM:SS`.
 * @returns {number} the seconds since midnight.
 */
export function parseClock(text) {
  const match = /^(\d{2}):(\d{2}):(\d{2})$/.exec(text ?? '');
  if (!match) throw new RaceError(`bad time ${JSON.stringify(text)}`);
  const [hours, minutes, seconds] = match.slice(1).map(Number);
  if (hours > 23 || minutes > 59 || seconds > 59) throw new RaceError(`bad time ${JSON.stringify(text)}`);
  return hours * 3600 + minutes * 60 + seconds;
}

/**
 * A duration written for people.
 * @param {number} seconds - whole seconds.
 * @returns {string} the duration as `H:MM:SS`, such as `0:41:07`.
 */
export function formatDuration(seconds) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${Math.floor(seconds / 3600)}:${pad(Math.floor(seconds / 60) % 60)}:${pad(seconds % 60)}`;
}
