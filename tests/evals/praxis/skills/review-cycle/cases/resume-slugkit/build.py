"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("checkout", "-q", "-b", "feature/issue-61")
write(
    "src/slug.js",
    "'use strict';\n\n// Lowercase ASCII letters and digits, with each run of anything else turned into one separator.\nfunction toSlug(text, separator = '-') {\n  return text\n    .toLowerCase()\n    .replace(/[^a-z0-9]+/g, separator)\n    .replace(new RegExp(`^${separator}+|${separator}+$`, 'g'), '');\n}\n\n// The slug cut to at most `max` characters.\nfunction trimToLength(slug, max) {\n  return slug.slice(0, max);\n}\n\nfunction slugify(text, options = {}) {\n  const slug = toSlug(text, options.separator);\n  return options.maxLength ? trimToLength(slug, options.maxLength) : slug;\n}\n\nmodule.exports = { slugify, toSlug, trimToLength };\n",
)
write(
    "test/slug.test.js",
    "'use strict';\n\nconst test = require('node:test');\nconst assert = require('node:assert');\nconst { slugify } = require('../src/slug');\n\ntest('joins words with a dash', () => {\n  assert.strictEqual(slugify('Hello, World!'), 'hello-world');\n});\n\ntest('cuts the slug to maxLength', () => {\n  assert.strictEqual(slugify('Hello World', { maxLength: 5 }), 'hello');\n});\n\ntest('joins words with the separator given', () => {\n  assert.strictEqual(slugify('Hello World', { separator: '_' }), 'hello_world');\n});\n",
)
git("add", "-A")
git("commit", "-q", "-m", "feat(slug): let callers choose the separator")
write(
    ".claude/workspace/issue-61/feature--issue-61/1.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\nNone found\n\n### Minor Issues\n1. **The README does not mention the separator option** -- `README.md:3`. Add a sentence.\n\n### Summary\nOne Minor finding.\n\nAnswer: fixed in the round-1 commit.\n",
)
write(
    ".claude/workspace/issue-61/feature--issue-61/2.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\nNone found\n\n### Minor Issues\n1. **The test names do not say what they check** -- `README.md:3`. Add a sentence.\n\n### Summary\nOne Minor finding.\n\nAnswer: fixed in the round-2 commit.\n",
)
write(
    ".claude/workspace/issue-61/feature--issue-61/cycle.md",
    "# Review cycle: feature/issue-61\n\nMode: raise\nBase: main\nRound: 2 (addressed)\nClean rounds in a row: 0\nRaised findings: none\nPR: none\n",
)
write(
    ".claude/workspace/issue-61/feature--issue-61/pr.md",
    "feat(slug): let callers choose the separator\n\nLet callers choose the slug separator.\n\nCloses #61\n",
)
