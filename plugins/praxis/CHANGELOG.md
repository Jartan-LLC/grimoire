# Changelog

## 1.5.1

- No user-visible change.

## 1.5.0

- New `comment-hygiene` skill: the comment rules (what to keep, delete or
  exempt; tombstones; retold facts; comment density) and
  `find-duplicate-comments.js` move out of `code-hygiene`, which keeps dead and
  duplicated code, naming, real implementations and scoped suppressions. The
  general reviewer loads both.
