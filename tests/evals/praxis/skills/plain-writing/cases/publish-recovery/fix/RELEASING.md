# Releasing

1. Bump `version` in `pyproject.toml` and add a `CHANGELOG.md` entry.
2. Merge the PR.
3. Tag the merge commit `v<version>` and push the tag.
4. Run `make publish` from the tag.

PyPI never accepts the same version twice. If an upload is broken, yank it on PyPI and release
the next patch version.
