/**
 * The records the invoicekit modules pass to one another.
 * @module
 */

/**
 * Digits after the decimal point in each currency's minor unit.
 * @type {Readonly<Record<string, number>>}
 */
export const CURRENCY_DIGITS = Object.freeze({
  EUR: 2,
  USD: 2,
  GBP: 2,
  CHF: 2,
  SEK: 2,
  DKK: 2,
  PLN: 2,
  CZK: 2,
  HUF: 2,
  JPY: 0,
  BHD: 3,
  KWD: 3,
});

/**
 * An amount of money. `amount` is a safe integer in the currency's minor unit: EUR 12.50 is
 * `{ amount: 1250, currency: "EUR" }`, JPY 300 is `{ amount: 300, currency: "JPY" }`.
 * @typedef {object} Money
 * @property {number} amount
 * @property {string} currency An ISO 4217 code listed in CURRENCY_DIGITS.
 */

/**
 * @typedef {"business"|"consumer"} PartyKind
 */

/**
 * A seller or buyer.
 * @typedef {object} Party
 * @property {string} name
 * @property {string[]} address
 * @property {string} country ISO 3166-1 alpha-2, upper case.
 * @property {string | null} vatId As written, or null when the party has none.
 * @property {PartyKind} kind
 */

/**
 * The VAT rate class a line falls in.
 * @typedef {"standard"|"reduced"|"super-reduced"|"zero"|"exempt"} TaxCategory
 */

/** @type {readonly TaxCategory[]} */
export const TAX_CATEGORIES = Object.freeze(["standard", "reduced", "super-reduced", "zero", "exempt"]);

/**
 * One invoice line.
 * @typedef {object} Line
 * @property {string} description
 * @property {number} quantity Up to three decimal places: 1.5 hours.
 * @property {Money} unitPrice Net of VAT.
 * @property {TaxCategory} category
 * @property {number} [discountPct] 0 to 100, up to two decimal places.
 */

/**
 * @typedef {"invoice"|"credit-note"} InvoiceKind
 */

/**
 * An invoice or credit note. Dates are ISO `YYYY-MM-DD` strings.
 * @typedef {object} Invoice
 * @property {InvoiceKind} kind
 * @property {string | null} number Null until the invoice is issued.
 * @property {string} issueDate
 * @property {string} dueDate
 * @property {Party} seller
 * @property {Party} buyer
 * @property {string} currency
 * @property {Line[]} lines
 * @property {string[]} notes
 * @property {string | null} credits For a credit note, the number of the invoice it credits.
 */

/** Input invoicekit refuses: a bad rate, an unknown currency, a number out of sequence. */
export class InvoiceError extends Error {
  /** @param {string} message */
  constructor(message) {
    super(message);
    this.name = "InvoiceError";
  }
}
