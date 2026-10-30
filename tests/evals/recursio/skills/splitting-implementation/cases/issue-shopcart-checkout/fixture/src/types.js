// The records the bookshop modules pass to one another. Money is always a whole number of
// cents of the shop's currency (pence: the shop sells in GBP), never a float.

/** @typedef {number} Money */

/**
 * A catalogue entry. Weight in grams, dimensions in centimetres. `backorder` allows selling it
 * when no warehouse has stock.
 * @typedef {{ sku: string, title: string, priceCents: Money, category: string, weightG: number,
 *   lengthCm: number, widthCm: number, heightCm: number, backorder: boolean }} Product
 */

/** @typedef {{ sku: string, quantity: number }} CartLine */

/** The kinds of promotion pricing knows. */
export const PROMOTION_KINDS = Object.freeze(["percent", "fixed", "buy_x_get_y", "tier", "bundle"]);

/**
 * A promotion. One with a `code` is a coupon and applies only when the customer enters it.
 * The fields after `stackable` depend on `kind`:
 * - percent: `percent` (1-100) and optionally `skus` or `category` to limit it
 * - fixed: `amountCents` off the cart, `minSubtotalCents`
 * - buy_x_get_y: `sku`, `buy`, `get`, `percentOff` (100 means free)
 * - tier: `sku`, `tiers` as [{ minQty, unitCents }]
 * - bundle: `skus` (one of each makes a set), `priceCents` per set
 * @typedef {{ id: string, kind: string, code?: string, exclusive: boolean, stackable: boolean,
 *   percent?: number, skus?: string[], category?: string, amountCents?: Money,
 *   minSubtotalCents?: Money, sku?: string, buy?: number, get?: number, percentOff?: number,
 *   tiers?: Array<{ minQty: number, unitCents: Money }>, priceCents?: Money }} Promotion
 */

/** @typedef {{ id: string, priority: number, countries: string[] }} Warehouse */

/** `country` is an ISO 3166-1 alpha-2 code; `postcode` as the customer typed it. */
/** @typedef {{ name: string, line1: string, city: string, postcode: string, country: string }} Address */

/**
 * One box as shipping packs it. `chargeableKg` is what the carrier bills.
 * @typedef {{ warehouse: string | null, items: CartLine[], weightG: number, lengthCm: number,
 *   widthCm: number, heightCm: number, chargeableKg: number }} Parcel
 */

/** The states an order moves through, in their usual order, then the two ends besides delivery. */
export const ORDER_STATES = Object.freeze([
  "placed",
  "paid",
  "packed",
  "shipped",
  "delivered",
  "cancelled",
  "refunded",
]);

/** @typedef {"placed" | "paid" | "packed" | "shipped" | "delivered" | "cancelled" | "refunded"} OrderState */

/** @typedef {{ type: string, at: string, detail: Record<string, unknown> }} OrderEvent */

/**
 * A priced order line: `totalCents` = quantity x unitCents - discountCents.
 * @typedef {{ sku: string, quantity: number, unitCents: Money, discountCents: Money,
 *   totalCents: Money }} OrderLine
 */

/**
 * An order. `at` times are ISO 8601 UTC strings.
 * @typedef {{ id: string, state: OrderState, lines: OrderLine[], shippingCents: Money,
 *   totalCents: Money, refundedCents: Money, address: Address, events: OrderEvent[] }} Order
 */

/** An error any module throws for a rule the input broke; `code` is stable, `message` is for people. */
export class ShopError extends Error {
  /**
   * @param {string} code
   * @param {string} message
   */
  constructor(code, message) {
    super(message);
    this.name = "ShopError";
    this.code = code;
  }
}
