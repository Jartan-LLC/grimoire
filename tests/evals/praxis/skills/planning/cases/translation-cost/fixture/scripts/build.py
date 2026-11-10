"""Render every help/<lang>/*.md to site/<lang>/."""

import pathlib

for page in pathlib.Path("help").glob("*/*.md"):
    print("render", page)
