// The records the recipebox modules pass to one another.

/**
 * A non-negative fraction in lowest terms, `den` > 0. 1 1/2 is { num: 3, den: 2 }.
 * @typedef {{ num: number, den: number }} Rational
 */

/**
 * An amount: one exact value, or a range such as the "2-3" of "2-3 eggs".
 * @typedef {{ kind: "exact", value: Rational }
 *   | { kind: "range", low: Rational, high: Rational }} Quantity
 */

/**
 * One ingredient line. `quantity` is null for "salt to taste"; `unit` is a key of UNITS, or
 * null for a count ("3 eggs"); `note` holds a parenthetical or trailing remark ("finely chopped").
 * @typedef {{ quantity: Quantity | null, unit: string | null, name: string, note: string | null }} Ingredient
 */

/**
 * A whole recipe. `section` groups ingredients under a heading such as "For the sauce", or is
 * null for ingredients listed before any heading.
 * @typedef {{ title: string, servings: number, ingredients: Array<Ingredient & { section: string | null }>, steps: string[] }} Recipe
 */

/**
 * Nutrients per 100 g of one food, as the nutrient table lists them. `gramsPerCup` lets a volume
 * be weighed and `gramsEach` a count ("2 eggs"); either is null when the table does not know it.
 * @typedef {{ name: string, kcal: number, proteinG: number, fatG: number, carbsG: number,
 *   sodiumMg: number, gramsPerCup: number | null, gramsEach: number | null }} NutrientRow
 */

/**
 * The canonical units. Every unit an ingredient carries is one of these keys. `dimension` says
 * what it measures; `base` is one unit in millilitres (volume) or grams (mass), null for a count.
 * "pinch" (1/16 tsp) and "dash" (1/8 tsp) are volumes; "clove" and "can" count things.
 */
export const UNITS = Object.freeze({
  tsp: Object.freeze({ dimension: "volume", system: "us", base: 4.92892159375 }),
  tbsp: Object.freeze({ dimension: "volume", system: "us", base: 14.78676478125 }),
  floz: Object.freeze({ dimension: "volume", system: "us", base: 29.5735295625 }),
  cup: Object.freeze({ dimension: "volume", system: "us", base: 236.5882365 }),
  pint: Object.freeze({ dimension: "volume", system: "us", base: 473.176473 }),
  quart: Object.freeze({ dimension: "volume", system: "us", base: 946.352946 }),
  gallon: Object.freeze({ dimension: "volume", system: "us", base: 3785.411784 }),
  pinch: Object.freeze({ dimension: "volume", system: "us", base: 0.308057599609375 }),
  dash: Object.freeze({ dimension: "volume", system: "us", base: 0.61611519921875 }),
  ml: Object.freeze({ dimension: "volume", system: "metric", base: 1 }),
  l: Object.freeze({ dimension: "volume", system: "metric", base: 1000 }),
  oz: Object.freeze({ dimension: "mass", system: "us", base: 28.349523125 }),
  lb: Object.freeze({ dimension: "mass", system: "us", base: 453.59237 }),
  g: Object.freeze({ dimension: "mass", system: "metric", base: 1 }),
  kg: Object.freeze({ dimension: "mass", system: "metric", base: 1000 }),
  clove: Object.freeze({ dimension: "count", system: null, base: null }),
  can: Object.freeze({ dimension: "count", system: null, base: null }),
});
