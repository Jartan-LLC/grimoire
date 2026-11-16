# notifier

Sends the shop's order and shipping emails.

## Install

Needs Python 3.9 or newer.

```bash
pip install -r requirements.txt
```

## Usage

Call `notifier.send.send(to, subject, body)` with a subject and body from
`notifier.templates`.

## Sending an email

To send an email, call `send()` from `notifier.send`, passing the recipient, the subject
and the body. `notifier.templates` builds the subject and body for each kind of email.
