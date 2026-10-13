# Changelog

## 1.5.2

- `comment-hygiene`: a standing hot-path measurement stays inline as a WHY; only
  a change's before/after numbers go to the PR body. The density re-read now asks
  whether each comment passes KEEP.
- The general reviewer rates comments that don't earn their place Minor, matching
  `review-severity`.

## 1.5.1

- No user-visible change.

## 1.5.0

- New `comment-hygiene` skill: the comment rules (what to keep, delete or
  exempt; tombstones; retold facts; comment density) and
  `find-duplicate-comments.js` move out of `code-hygiene`, which keeps dead and
  duplicated code, naming, real implementations and scoped suppressions. The
  general reviewer loads both.
