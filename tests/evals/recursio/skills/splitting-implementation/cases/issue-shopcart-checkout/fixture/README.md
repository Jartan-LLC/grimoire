# bookshop

The order engine behind our online bookshop: prices a cart, holds stock for it, quotes shipping,
and tracks the order from payment to delivery. ES modules, no dependencies, Node 24. Money is a
whole number of cents (pence) everywhere; no module keeps an amount as a float.

## Types

`src/types.js` holds the JSDoc types the modules share, `Product`, `CartLine`, `Promotion`,
`Warehouse`, `Address`, `Parcel`, `Order`, `OrderLine`, `OrderEvent` and `OrderState`, the constants
`PROMOTION_KINDS` and `ORDER_STATES`, and `ShopError(code, message)`, which every module throws
for a broken rule. The pricing, inventory, orders and shipping modules use these and nothing of each
other; checkout uses them all.

## Pricing (`src/pricing.js`)

`priceCart(lines, products, promotions, codes = [])` returns `{ lines, applied, subtotalCents,
discountCents, totalCents }`: one `OrderLine` per cart line in cart order, and `applied` as
`[{ id, discountCents }]` sorted by id. A line for an unknown sku throws `unknown_sku`; a quantity
that is not a positive whole number throws `bad_quantity`.

- **Kinds.** `percent` takes `percent` off each matching unit (all lines, or only `skus`, or only
  `category`). `fixed` takes `amountCents` off the cart when the subtotal after line discounts is
  at least `minSubtotalCents`, never more than that subtotal. `buy_x_get_y` makes `get` units of
  `sku` `percentOff` cheaper for every `buy + get` units in the cart (buy 2 get 1 free on 7 units
  discounts 2). `tier` sets the unit price of `sku` to the highest tier whose `minQty` the
  quantity reaches. `bundle` prices each complete set of `skus` (one of each) at `priceCents`,
  the discount being the sets' list price minus that.
- **Units are used once.** Within a combination, unit promotions take units in the order bundle,
  then buy_x_get_y, then tier, and a unit one of them took is not available to the next.
  `percent` then applies to what each unit still costs, and `fixed` last to the cart.
- **Coupons.** A promotion with a `code` applies only when that code is in `codes`, matched
  case-insensitively with spaces trimmed; an unknown code throws `unknown_code`. At most one
  coupon applies unless every entered coupon is `stackable`.
- **Exclusivity.** An `exclusive` promotion combines with no other promotion that discounts any of
  the same lines; an exclusive `fixed` combines with nothing at all.
- **Best combination.** Of all the combinations the rules allow (at most 12 promotions are ever
  offered, so every subset can be tried), the customer gets the one with the largest total
  discount; a tie goes to fewer promotions, then to the one whose sorted ids come first.
- **Rounding.** A percent discount is worked per line and rounded half up to the cent (15% of
  3 x 399 is 179.55, so 180). A `fixed` discount is shared across lines in proportion to their
  totals by the largest-remainder method, ties to the earlier line, so the line discounts add up
  to it exactly. No line total goes below 0.

## Inventory (`src/inventory.js`)

The state is a plain object that every function returns anew; inputs are never mutated.

- `createInventory(warehouses, stock)` takes `Warehouse`s and `[{ sku, warehouse, onHand }]`.
  An unknown warehouse or a negative count throws `bad_stock`.
- `available(inv, sku, now)` returns `{ [warehouseId]: count }`: on hand minus the unexpired
  reservations. `now` is an ISO string; time only moves through the arguments.
- `allocate(inv, lines, country, now)` returns `{ picks, backorders, unavailable }` without
  holding anything. Only warehouses whose `countries` include the destination take part. If one
  warehouse can fill every line, the one with the lowest `priority` number does (ties by id).
  Otherwise each line takes from warehouses in priority order, as much as each has, so a line can
  come from several. A shortfall goes to `backorders` when the product allows backorder and to
  `unavailable` (`[{ sku, short }]`) when it does not. `picks` are `[{ sku, warehouse, quantity }]`
  sorted by warehouse, then sku.
- `reserve(inv, orderId, picks, now, ttlMinutes = 15)` holds the picks until `now` plus the ttl;
  reserving an order that already holds stock throws `already_reserved`, and picking more than is
  available throws `insufficient_stock` naming the sku and warehouse.
- `extend(inv, orderId, now, ttlMinutes = 15)` renews a hold; an expired or unknown one throws
  `no_reservation`.
- `release(inv, orderId)` drops an order's hold (an unknown order changes nothing), `expire(inv,
  now)` drops every hold that ran out and returns `{ inv, released: [orderId] }`, and
  `commit(inv, orderId)` turns a hold into a real decrement of `onHand`.
- `restock(inv, sku, warehouse, quantity)` adds stock to one warehouse.

## Orders (`src/orders.js`)

- `placeOrder(id, lines, shippingCents, address, at)` creates an order in `placed` with the
  event `placed`; `totalCents` is the line totals plus shipping.
- `transition(order, action, at, detail = {})` returns the new order with one event appended.
  Allowed moves: `pay` placed -> paid (`detail.amountCents` must equal `totalCents`, else
  `amount_mismatch`); `pack` paid -> packed; `ship` packed -> shipped (`detail.carrier` and
  `detail.tracking` required, else `missing_tracking`); `deliver` shipped -> delivered; `cancel`
  from placed or paid -> cancelled, a paid order getting a `refund` event for the full amount and
  `refundedCents` set. Any other move throws `invalid_transition` with the message
  `cannot ship an order that is placed` (the action and the state named). An `at` earlier than
  the last event throws `time_went_back`.
- `refund(order, { lines, shippingCents = 0, reason }, at)` refunds part of a shipped or
  delivered order. Each `{ sku, quantity }` refunds that many units at the line's paid price per
  unit: floor(totalCents / quantity) a unit, the last unit of the line carrying the remainder so a
  whole line refunds exactly its total. Refunding more units than remain unrefunded throws
  `over_refund`; refunding shipping is allowed only once every unit has been refunded or when the
  reason is `damaged`. A delivered order can be refunded for 30 days after its `delivered` event;
  later throws `return_window_closed`. When `refundedCents` reaches `totalCents` the state becomes
  `refunded`. Each call adds one `refund` event with the lines and amount.
- `refundable(order)` returns the units and cents still refundable per line.
- `replay(events)` rebuilds an order from its events alone and must equal the order they came
  from; a history that breaks the rules throws the same errors.

## Shipping (`src/shipping.js`)

- **Zones.** `zoneFor(address)`: `GB` is `uk`, except postcodes whose outward code starts with
  `BT`, `HS`, `IV`, `KW`, `PH` or `ZE`, or with `PA` and a district from 20 to 49 (`PA34`), which
  are `uk-remote`. Postcodes are matched upper-cased with spaces removed, the longest rule
  winning. `IE`, `FR`, `DE`, `NL`, `BE`, `ES`, `IT`, `PT`, `AT`, `DK`, `SE`, `FI`, `PL` and `CZ`
  are `eu`; any other country is `world`. An empty or malformed GB postcode throws `bad_postcode`.
- **Rates** in pence by chargeable weight up to and including each limit:

  | Zone | 1 kg | 2 kg | 5 kg | 10 kg | 20 kg |
  |------|------|------|------|-------|-------|
  | uk | 395 | 495 | 695 | 995 | 1495 |
  | uk-remote | 995 | 1095 | 1295 | 1595 | 2095 |
  | eu | 850 | 1100 | 1600 | 2400 | 3800 |
  | world | 1400 | 1950 | 3100 | 5200 | 8500 |

- **Packing.** `pack(items, products, warehouse = null)` puts units into parcels of at most 20 kg
  actual weight, heaviest first, each into the first parcel it fits (first-fit decreasing, ties
  by sku). A single unit over 20 kg throws `too_heavy`. A parcel's length and width are the
  largest of its units', and its height the sum of their heights.
- **Chargeable weight** is the larger of the actual weight and the dimensional weight, length x
  width x height / 5000 in kg, rounded up to the next 0.1 kg.
- `quote(parcels, address, goodsCents)` returns `{ zone, parcels, costCents, free }`: the sum of
  each parcel's rate, or 0 with `free: true` for the `uk` zone when `goodsCents` is at least
  5000. `uk-remote` never ships free.

## Checkout (`src/checkout.js`)

`checkout(cart, ctx)` with `ctx` holding `catalog`, `promotions`, `codes`, `inventory`,
`address`, `orderId` and `now`:

1. Empty carts throw `empty_cart`. Price the cart.
2. Allocate stock for the address's country; any `unavailable` line throws `out_of_stock` with
   the skus, and nothing is held.
3. Pack each warehouse's picks into its own parcels (backordered units ship from the
   highest-priority warehouse later, packed as their own group) and quote them all together, so
   the free-shipping threshold applies to the whole order's goods total after discounts.
4. Reserve the picks and place the order.

It returns `{ order, inventory, quote, backorders }`. `confirmPayment(state, amountCents, at)`
pays the order and commits its reservation; `cancelCheckout(state, at)` cancels it and releases
the hold. A reservation that expired before payment makes `confirmPayment` throw
`reservation_expired` and leaves the order placed.

## Status

Only `src/types.js` exists.
