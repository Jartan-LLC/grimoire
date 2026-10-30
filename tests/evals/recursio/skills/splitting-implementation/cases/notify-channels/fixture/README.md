# notifier

Sends a message through one or more channels.

Every channel has `send(message)`, where `message` is `{ text, priority, to }`, and resolves to
`{ ok, id }` or rejects with a `ChannelError` (`src/channel.js`). `src/console.js` is the one
channel so far.

## To add

- **Email** (`src/email.js`): through an injected transport with `sendMail({ to, subject, text })`;
  the subject is the message's first line, cut at 78 characters.
- **Webhook** (`src/webhook.js`): POSTs the message as JSON through an injected `fetch`; retries
  once on a 5xx answer, and a 4xx answer is a `ChannelError`.
- **SMS** (`src/sms.js`): through an injected client with `create({ to, body })`; a text over 160
  characters goes out as numbered segments ("(1/3) ...").
- **Router** (`src/router.js`): picks channels by priority -- `low`: console; `normal`: email;
  `high`: email and SMS; `critical`: every channel. It returns each channel's result, and one
  channel failing does not stop the others.
