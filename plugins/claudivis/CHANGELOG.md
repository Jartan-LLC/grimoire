# Changelog

Earlier versions: the `claudivis--v*` tags.

## 1.1.2

- The `claude-config` skill now tells workflow skills to set neither invocation
  field: `disable-model-invocation: true` left an unprefixed `/name` with nothing
  to run. Knowledge skills set `user-invocable: false`.
