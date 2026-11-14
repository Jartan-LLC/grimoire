"""The feeds file: one URL per line, blank lines and # comments skipped."""


def read_feeds(path: str) -> list[str]:
    """The feed URLs in `path`, in file order."""
    with open(path) as handle:
        lines = (line.strip() for line in handle)
        return [line for line in lines if line and not line.startswith("#")]
