"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


write(
    ".claude/workspace/issue-67/plan.md",
    "# Plan: checkout (#67)\n\n## Steps\n\n1. `src/pricing.js`: `priceCart(lines, products, promotions, codes)` with the five promotion kinds,\n   coupons, exclusivity, the best combination and per-line rounding, with `test/pricing.test.js`.\n2. `src/inventory.js`: stock per warehouse, `allocate`, `reserve`, `extend`, `release`, `expire` and\n   `commit`, with `test/inventory.test.js`.\n3. `src/orders.js`: `placeOrder`, `transition`, `refund`, `refundable` and `replay`, with\n   `test/orders.test.js`.\n4. `src/shipping.js`: `zoneFor`, the rate table, `pack` and `quote`, with `test/shipping.test.js`.\n5. `src/checkout.js`: `checkout`, `confirmPayment` and `cancelCheckout` over the four modules above,\n   with `test/checkout.test.js`.\n\n## Verification\n\n- `npm test`\n",
)
