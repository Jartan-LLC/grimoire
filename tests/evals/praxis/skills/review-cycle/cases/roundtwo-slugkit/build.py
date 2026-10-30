"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("checkout", "-q", "-b", "feature/issue-73")
write(
    "src/slug.js",
    "'use strict';\n\n// ASCII letters and digits, lowercased unless `lowercase` is false, with each run of anything else turned into one dash.\nfunction toSlug(text, lowercase = true) {\n  const source = lowercase ? text.toLowerCase() : text;\n  return source\n    .replace(/[^a-z0-9]+/g, '-')\n    .replace(/^-+|-+$/g, '');\n}\n\n// The slug cut to at most `max` characters.\nfunction trimToLength(slug, max) {\n  return slug.slice(0, max);\n}\n\nfunction slugify(text, options = {}) {\n  const slug = toSlug(text, options.lowercase);\n  return options.maxLength ? trimToLength(slug, options.maxLength) : slug;\n}\n\nmodule.exports = { slugify, toSlug, trimToLength };\n",
)
git("add", "-A")
git("commit", "-q", "-m", "feat(slug): let callers keep capital letters")
write(
    ".claude/workspace/issue-73/feature--issue-73/1.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\n1. **Capital letters are dropped when lowercase is false** -- `src/slug.js:7`. The character class `[^a-z0-9]` still matches `A-Z`, so each capital becomes a dash: `slugify('Hello World', { lowercase: false })` returns `ello-orld`. No test covers the option.\n\n### Minor Issues\n1. **The README does not mention the lowercase option** -- `README.md:3`. Add a sentence.\n\n### Summary\nOne Important and one Minor finding.\n",
)
write(
    "src/slug.js",
    "'use strict';\n\n// ASCII letters and digits, lowercased unless `lowercase` is false, with each run of anything else turned into one dash.\nfunction toSlug(text, lowercase = true) {\n  const source = lowercase ? text.toLowerCase() : text;\n  return source\n    .replace(/[^A-Za-z0-9]+/g, '-')\n    .replace(/^-+|-+$/g, '');\n}\n\n// The slug cut to at most `max` characters.\nfunction trimToLength(slug, max) {\n  return slug.slice(0, max);\n}\n\nfunction slugify(text, options = {}) {\n  const slug = toSlug(text, options.lowercase);\n  return options.maxLength ? trimToLength(slug, options.maxLength) : slug;\n}\n\nmodule.exports = { slugify, toSlug, trimToLength };\n",
)
write(
    "test/slug.test.js",
    "'use strict';\n\nconst test = require('node:test');\nconst assert = require('node:assert');\nconst { slugify } = require('../src/slug');\n\ntest('joins words with a dash', () => {\n  assert.strictEqual(slugify('Hello, World!'), 'hello-world');\n});\n\ntest('cuts the slug to maxLength', () => {\n  assert.strictEqual(slugify('Hello World', { maxLength: 5 }), 'hello');\n});\n\ntest('keeps capital letters when lowercase is false', () => {\n  assert.strictEqual(slugify('Hello World', { lowercase: false }), 'Hello-World');\n});\n",
)
git("add", "-A")
git(
    "commit",
    "-q",
    "-m",
    "fix(slug): keep capitals when lowercase is false",
    "-m",
    "The character class still left out A-Z, so with lowercase: false each capital turned into a dash and 'Hello World' came out as 'ello-orld'.",
)
write(
    "README.md",
    "# slugkit\n\n`slugify('Hello, World!')` returns `hello-world`. Pass `{ maxLength: n }` to cut the slug to n characters, and `{ lowercase: false }` to keep capital letters: `slugify('Hello World', { lowercase: false })` returns `Hello-World`.\n\n## Development\n\nRun the tests with `npm test`.\n",
)
git("add", "-A")
git("commit", "-q", "-m", "docs(readme): describe the lowercase option")
