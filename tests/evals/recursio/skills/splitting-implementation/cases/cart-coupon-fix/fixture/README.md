# shopcart

Basket totals for the shop. Amounts are whole cents.

- `src/cart.js`: the basket's net, discount, VAT and total.
- `src/tax.js`: VAT by the customer's country.
- `src/coupon.js`: what a coupon takes off.

A coupon comes off the net price, before VAT, and VAT is charged on what is left. A coupon's
minimum spend is checked against the shelf price, VAT included.
