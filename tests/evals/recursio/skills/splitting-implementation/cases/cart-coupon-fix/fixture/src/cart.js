import { discountCents } from "./coupon.js";
import { vatCents } from "./tax.js";

/** @typedef {import("./coupon.js").Coupon} Coupon */
/** @typedef {{ sku: string, unitCents: number, quantity: number }} Line */

/**
 * The basket's net amount: every line's unit price times its quantity.
 * @param {Line[]} lines
 */
export function subtotalCents(lines) {
  return lines.reduce((sum, line) => sum + line.unitCents * line.quantity, 0);
}

/**
 * The basket's totals. The coupon comes off the net, and VAT is charged on what is left.
 * @param {Line[]} lines
 * @param {string} country
 * @param {Coupon | null} [coupon]
 */
export function cartTotals(lines, country, coupon = null) {
  const netCents = subtotalCents(lines);
  const discount = coupon ? discountCents(coupon, netCents, country) : 0;
  const taxable = netCents - discount;
  const vat = vatCents(taxable, country);
  return { netCents, discountCents: discount, vatCents: vat, totalCents: taxable + vat };
}
