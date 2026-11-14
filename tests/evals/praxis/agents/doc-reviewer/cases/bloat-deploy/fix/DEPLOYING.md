# Deploying

Every merge to `main` builds a release candidate.

## Deploy a release

Run `make ship` from `main`. It pushes the image, runs the migrations and switches traffic to the
new version. A 502 from the registry is retried three times. When no migration changed, the migration
step is skipped. On a shallow clone the script fetches the tags first.
