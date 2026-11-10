class Client:
    def __init__(self, key):
        self.key = key

    def get_items(self, page=1):
        """Return one page of items."""
        return self._get("/items", page=page)

    def _get(self, path, **params):
        raise NotImplementedError
