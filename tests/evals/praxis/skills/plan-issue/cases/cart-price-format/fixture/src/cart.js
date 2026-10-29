// The cart summary shown beside the checkout button.

function cartTotal(cart) {
  return cart.items.reduce((sum, item) => sum + item.qty * item.unitCents, 0);
}

function cartSummary(cart) {
  const count = cart.items.reduce((n, item) => n + item.qty, 0);
  return {
    lines: cart.items.map((item) => `${item.qty} x ${item.name}: ${(item.qty * item.unitCents) / 100}`),
    footer: `${count} items. Total: ${cartTotal(cart) / 100}`,
  };
}

module.exports = { cartTotal, cartSummary };
