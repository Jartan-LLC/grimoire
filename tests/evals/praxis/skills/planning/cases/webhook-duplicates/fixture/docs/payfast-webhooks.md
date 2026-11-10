# PayFast webhooks

- PayFast POSTs JSON events to our webhook URL and retries until it gets a 2xx answer
  within 10 seconds, for up to three days. An event can therefore arrive more than once,
  and events can arrive out of order.
- Each event has a unique `id` and a `type`, such as `payment.succeeded`, with the order
  reference in `data.reference`.
- The `PayFast-Signature` header is the hex HMAC-SHA256 of the raw body with the webhook
  secret.
