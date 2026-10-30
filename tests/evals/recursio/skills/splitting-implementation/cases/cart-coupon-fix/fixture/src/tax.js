/** Standard VAT rate by country code. */
export const VAT_RATES = { GB: 0.2, DE: 0.19, FR: 0.2, IE: 0.23 };

/**
 * The VAT rate for `country`.
 * @param {string} country
 * @returns {number}
 */
export function vatRate(country) {
  const rate = VAT_RATES[country];
  if (rate === undefined) throw new Error(`no VAT rate for ${country}`);
  return rate;
}

/**
 * VAT on a net amount, rounded to the cent.
 * @param {number} netCents
 * @param {string} country
 */
export function vatCents(netCents, country) {
  return Math.round(netCents * vatRate(country));
}

/**
 * A net amount with its VAT added: the shelf price.
 * @param {number} netCents
 * @param {string} country
 */
export function grossCents(netCents, country) {
  return netCents + vatCents(netCents, country);
}
