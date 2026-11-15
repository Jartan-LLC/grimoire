class Client:
    def __init__(self, host):
        self.host = host
        self.handlers = {}

    def subscribe(self, topic, cb):
        """Call `cb(message)` for every message on `topic`."""
        self.handlers.setdefault(topic, []).append(cb)

    def deliver(self, topic, message):
        for handler in self.handlers.get(topic, []):
            handler(message)
