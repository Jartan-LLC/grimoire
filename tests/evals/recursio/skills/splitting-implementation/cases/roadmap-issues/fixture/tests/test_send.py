from mailroom.send import send_issue


class Recorder:
    def __init__(self):
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append(to)


def test_send_issue_reaches_everyone():
    transport = Recorder()
    assert send_issue(["a@x", "b@x"], "s", "b", transport) == 2
    assert transport.sent == ["a@x", "b@x"]
