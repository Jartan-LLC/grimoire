import { grossCents } from "./tax.js";

/**
 * @typedef {{ kind: "percent", percent: number, minSpendCents?: number }
 *   | { kind: "fixed", cents: number, minSpendCents?: number }} Coupon
 */

/**
 * What a coupon takes off a basket's net amount, in cents. A percent coupon takes its percentage
 * of the net; a fixed coupon takes its amount, but never more than the net. A coupon whose minimum
 * spend the shelf price (VAT included) does not reach takes nothing.
 * @param {Coupon} coupon
 * @param {number} netCents
 * @param {string} country
 * @returns {number}
 */
export function discountCents(coupon, netCents, country) {
  const shelfCents = grossCents(netCents, country);
  if (shelfCents < (coupon.minSpendCents ?? 0)) return 0;
  if (coupon.kind === "percent") {
    return Math.round((shelfCents * coupon.percent) / 100);
  }
  return Math.min(coupon.cents, netCents);
}
