"""Send one newsletter issue to every subscriber."""


def send_issue(subscribers: list[str], subject: str, body: str, transport) -> int:
    """Send to each subscriber through `transport.send(to, subject, body)`; return how many went out."""
    sent = 0
    for address in subscribers:
        transport.send(address, subject, body)
        sent += 1
    return sent
