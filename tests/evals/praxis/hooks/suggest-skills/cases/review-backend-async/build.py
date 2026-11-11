"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess

BRANCH = "feature/refresh-prices"
SUBJECT = "feat(api): refresh cached prices from the supplier"
BODY = "The supplier's prices change during the day; the cache now refreshes on request."
FILES = {
    "pricesvc/refresh.py": '"""Refresh the cached prices from the supplier\'s API."""\n\nimport asyncio\nimport json\nimport time\nimport urllib.request\n\nfrom pricesvc.cache import PRICES\n\nSUPPLIER = "https://supplier.example/api/price/"\n\n\nasync def fetch(sku: str) -> float:\n    """The supplier\'s price for `sku`."""\n    with urllib.request.urlopen(SUPPLIER + sku, timeout=5) as response:\n        return json.load(response)["price"]\n\n\nasync def refresh(skus: list[str]) -> None:\n    """Fetch every SKU\'s price into the cache."""\n    results = await asyncio.gather(*(fetch(s) for s in skus), return_exceptions=True)\n    for sku, price in zip(skus, results):\n        if isinstance(price, float):\n            PRICES[sku] = price\n        time.sleep(0.2)  # the supplier allows five requests a second\n'
}


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for path, text in FILES.items():
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
git("add", "-A")
git("commit", "-q", "-m", SUBJECT, "-m", BODY)
