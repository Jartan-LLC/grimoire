// Helpers.

const SMALL_WORDS = new Set(["a", "an", "and", "of", "in", "on", "the", "to"]);

/** @param {string} text */
export function slugify(text) {
  return text
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/**
 * `text` cut to at most `max` characters at a word boundary, with an ellipsis when cut.
 * @param {string} text
 * @param {number} max
 */
export function truncate(text, max) {
  if (text.length <= max) return text;
  const cut = text.slice(0, max - 3);
  const space = cut.lastIndexOf(" ");
  return `${space > 0 ? cut.slice(0, space) : cut}...`;
}

/** @param {string} text */
export function titleCase(text) {
  return text
    .split(" ")
    .map((word, i) => (i > 0 && SMALL_WORDS.has(word) ? word : word.charAt(0).toUpperCase() + word.slice(1)))
    .join(" ");
}

/**
 * @template T
 * @param {T[]} items
 * @param {number} size
 * @returns {T[][]}
 */
export function chunk(items, size) {
  const out = [];
  for (let i = 0; i < items.length; i += size) out.push(items.slice(i, i + size));
  return out;
}

/**
 * The items with the first of each key kept, in order.
 * @template T
 * @param {T[]} items
 * @param {(item: T) => unknown} key
 */
export function uniqueBy(items, key) {
  const seen = new Set();
  return items.filter((item) => {
    const k = key(item);
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

/**
 * @template T
 * @param {T[]} items
 * @param {(item: T) => string} key
 * @returns {Map<string, T[]>}
 */
export function groupBy(items, key) {
  const groups = new Map();
  for (const item of items) {
    const k = key(item);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(item);
  }
  return groups;
}

/** @param {string} iso a `YYYY-MM-DD` date */
export function parseDate(iso) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) throw new Error(`not a date: ${iso}`);
  return new Date(`${iso}T00:00:00Z`);
}

/** @param {Date} date */
export function isoDate(date) {
  return date.toISOString().slice(0, 10);
}

/** @param {Date} date the date's `YYYY-MM`, for the archive */
export function monthKey(date) {
  return isoDate(date).slice(0, 7);
}

/**
 * @param {Date} date
 * @param {number} days
 */
export function addDays(date, days) {
  return new Date(date.getTime() + days * 86400000);
}
