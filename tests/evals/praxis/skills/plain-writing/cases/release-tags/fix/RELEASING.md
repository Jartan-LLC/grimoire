# Releasing

Each package carries its version in `pyproject.toml`. Bump it in the PR that changes the package,
with an entry in its `CHANGELOG.md`.

## Tag a release

After the PR merges, run `make verify`, then `scripts/tag-release.sh` from `main`. It tags each
package whose version is not tagged yet, as `<name>--v<version>`, and pushes the tags; the release
workflow then publishes each one.

## Troubleshooting

If the push fails with HTTP 403 after a workflow file changed, run `gh auth refresh -s workflow`
and run the script again.
