# Releasing

Run `scripts/release.sh <version>` from `main`. It tags the version and pushes the tag.

## Troubleshooting

If the push fails with HTTP 403 after a workflow file changed, run `gh auth refresh -s workflow`
and run the script again.
