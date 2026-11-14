"""Check a page's links and report the broken ones."""

import asyncio

from linkcheck.net import head


def check_all(urls: list[str]) -> dict[str, int]:
    """Each URL's status code, in the order given."""
    results: dict[str, int] = {}
    for url in urls:
        results[url] = asyncio.run(head(url))
    return results


def broken(urls: list[str]) -> list[str]:
    """The URLs that did not answer 200."""
    return [url for url, status in check_all(urls).items() if status != 200]
