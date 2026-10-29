"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("checkout", "-q", "-b", "feature/issue-67")
write(
    "src/slug.js",
    "'use strict';\n\n// Lowercase ASCII letters and digits, with each run of anything else turned into one dash.\nfunction toSlug(text) {\n  return text\n    .toLowerCase()\n    .replace(/[^a-z0-9]+/g, '-')\n    .replace(/^-+|-+$/g, '');\n}\n\n// The slug cut to at most `max` characters.\nfunction trimToLength(slug, max) {\n  if (slug.length <= max) return slug;\n  return slug.slice(0, slug.lastIndexOf('-', max));\n}\n\nfunction slugify(text, options = {}) {\n  const slug = toSlug(text);\n  return options.maxLength ? trimToLength(slug, options.maxLength) : slug;\n}\n\nmodule.exports = { slugify, toSlug, trimToLength };\n",
)
write(
    "test/slug.test.js",
    "'use strict';\n\nconst test = require('node:test');\nconst assert = require('node:assert');\nconst { slugify } = require('../src/slug');\n\ntest('joins words with a dash', () => {\n  assert.strictEqual(slugify('Hello, World!'), 'hello-world');\n});\n\ntest('cuts the slug to maxLength', () => {\n  assert.strictEqual(slugify('Hello World', { maxLength: 5 }), 'hello');\n});\n\ntest('ends a cut slug on a whole word', () => {\n  assert.strictEqual(slugify('Hello big world', { maxLength: 10 }), 'hello-big');\n});\n",
)
git("add", "-A")
git("commit", "-q", "-m", "feat(slug): end a cut slug on a whole word")
write(
    "src/slug.js",
    "'use strict';\n\n// Lowercase ASCII letters and digits, with each run of anything else turned into one dash.\nfunction toSlug(text) {\n  return text\n    .toLowerCase()\n    .replace(/[^a-z0-9]+/g, '-')\n    .replace(/^-+|-+$/g, '');\n}\n\n// The slug cut to at most `max` characters.\nfunction trimToLength(slug, max) {\n  if (slug.length <= max) return slug;\n  const end = slug.lastIndexOf('-', max);\n  return slug.slice(0, end > 0 ? end : max);\n}\n\nfunction slugify(text, options = {}) {\n  const slug = toSlug(text);\n  return options.maxLength ? trimToLength(slug, options.maxLength) : slug;\n}\n\nmodule.exports = { slugify, toSlug, trimToLength };\n",
)
write(
    "test/slug.test.js",
    "'use strict';\n\nconst test = require('node:test');\nconst assert = require('node:assert');\nconst { slugify } = require('../src/slug');\n\ntest('joins words with a dash', () => {\n  assert.strictEqual(slugify('Hello, World!'), 'hello-world');\n});\n\ntest('cuts the slug to maxLength', () => {\n  assert.strictEqual(slugify('Hello World', { maxLength: 5 }), 'hello');\n});\n\ntest('ends a cut slug on a whole word', () => {\n  assert.strictEqual(slugify('Hello big world', { maxLength: 10 }), 'hello-big');\n});\n\ntest('cuts a long first word at maxLength', () => {\n  assert.strictEqual(slugify('Supercalifragilistic', { maxLength: 5 }), 'super');\n});\n",
)
write(
    "README.md",
    "# slugkit\n\n`slugify('Hello, World!')` returns `hello-world`. Pass `{ maxLength: n }` to cut the slug to at most n characters. A slug cut by `maxLength` ends on a whole word.\n\n## Development\n\nRun the tests with `npm test`.\n",
)
git("add", "-A")
git(
    "commit",
    "-q",
    "-m",
    "fix(slug): cut a slug with no dash in reach at maxLength",
    "-m",
    "When the first word was longer than maxLength, lastIndexOf found no dash and returned -1, and slice(0, -1) kept all but the last letter. The README now says a cut slug ends on a whole word.",
)
write(
    "src/slug.js",
    "'use strict';\n\n// Lowercase ASCII letters and digits, with each run of anything else turned into one dash.\nfunction toSlug(text) {\n  return text\n    .toLowerCase()\n    .replace(/[^a-z0-9]+/g, '-')\n    .replace(/^-+|-+$/g, '');\n}\n\n// The slug cut to at most `max` characters: at the last dash that fits, or at `max` when none does.\nfunction trimToLength(slug, max) {\n  if (slug.length <= max) return slug;\n  const end = slug.lastIndexOf('-', max);\n  return slug.slice(0, end > 0 ? end : max);\n}\n\nfunction slugify(text, options = {}) {\n  const slug = toSlug(text);\n  return options.maxLength ? trimToLength(slug, options.maxLength) : slug;\n}\n\nmodule.exports = { slugify, toSlug, trimToLength };\n",
)
git("add", "-A")
git("commit", "-q", "-m", "docs(slug): say where trimToLength cuts")
write(
    ".claude/workspace/issue-67/feature--issue-67/1.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\n1. **A slug with no dash within maxLength is not cut** -- `src/slug.js:14`. When the first word is longer than `maxLength`, `lastIndexOf('-', max)` returns -1 and `slice(0, -1)` keeps all but the last letter: `slugify('Supercalifragilistic', { maxLength: 5 })` returns `supercalifragilisti`.\n\nAnswer: fixed in the round-1 commit.\n\n### Minor Issues\n1. **The README does not say a cut slug ends on a whole word** -- `README.md:3`. Add a sentence.\n\nAnswer: fixed in the round-1 commit.\n\n### Summary\nOne Important and one Minor finding.\n",
)
write(
    ".claude/workspace/issue-67/feature--issue-67/2.md",
    '## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\nNone found\n\n### Minor Issues\n1. **The comment on trimToLength does not say where it cuts** -- `src/slug.js:11`. It still reads "The slug cut to at most `max` characters", though the function now cuts at the last dash that fits.\n\nAnswer: fixed in the round-2 commit.\n\n### Summary\nOne Minor finding.\n',
)
write(
    ".claude/workspace/issue-67/feature--issue-67/cycle.md",
    "# Review cycle: feature/issue-67\n\nMode: decide\nBase: main\nRound: 2 (addressed)\nClean rounds in a row: 1\nRaised findings: none\nDecided findings: none\nPR: none\n",
)
write(
    ".claude/workspace/issue-67/feature--issue-67/pr.md",
    "feat(slug): end a cut slug on a whole word\n\nslugify() with maxLength now cuts at the last dash that fits, so a cut slug no longer ends in a dash or halfway through a word.\n\nCloses #67\n",
)
