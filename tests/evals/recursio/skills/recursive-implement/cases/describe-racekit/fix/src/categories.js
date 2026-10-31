// Age categories.
import { RaceError } from './clock.js';

/**
 * A runner's age for the race.
 * @param {number} born - the year of birth.
 * @param {number} year - the race's year.
 * @returns {number} the age on 31 December of the race's year.
 */
export function ageOn(born, year) {
  return year - born;
}

/**
 * A runner's category.
 * @param {number} born - the year of birth.
 * @param {string} sex - `F` or `M`.
 * @param {number} year - the race's year.
 * @returns {string} the category, such as `FSEN` or `MV45`.
 */
export function category(born, sex, year) {
  const age = ageOn(born, year);
  if (age < 10) throw new RaceError(`age ${age} is under 10`);
  if (age < 20) return `${sex}U20`;
  if (age < 35) return `${sex}SEN`;
  return `${sex}V${Math.min(70, Math.floor(age / 5) * 5)}`;
}

function bandOrder(band) {
  if (band === 'U20') return 0;
  if (band === 'SEN') return 1;
  return Number(band.slice(1));
}

/**
 * Sort order for categories.
 * @param {string} a - a category.
 * @param {string} b - another category.
 * @returns {number} below 0 when `a` comes first, above 0 when `b` does.
 */
export function compareCategories(a, b) {
  if (a[0] !== b[0]) return a[0] === 'F' ? -1 : 1;
  return bandOrder(a.slice(1)) - bandOrder(b.slice(1));
}
