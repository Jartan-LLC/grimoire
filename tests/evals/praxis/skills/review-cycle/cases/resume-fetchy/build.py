"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("checkout", "-q", "-b", "feature/issue-44")
write(
    "src/retry.js",
    "'use strict';\n\nconst DELAY_MS = 100;\nconst MAX_ATTEMPTS = 3;\n\n// Whether a failed attempt is worth another try: any error, for now.\nfunction shouldRetry(error) {\n  return Boolean(error);\n}\n\n// Seconds from a Retry-After header, or null when it is missing or not a number.\nfunction parseRetryAfter(value) {\n  const seconds = Number(value);\n  return Number.isFinite(seconds) ? seconds : null;\n}\n\nfunction sleep(ms) {\n  return new Promise((resolve) => setTimeout(resolve, ms));\n}\n\nasync function fetchWithRetry(url, options = {}, fetchImpl = globalThis.fetch) {\n  let lastError;\n  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {\n    try {\n      const response = await fetchImpl(url, options);\n      if (!response.ok) {\n        const error = new Error(`HTTP ${response.status}`);\n        error.status = response.status;\n        error.retryAfter = response.headers && response.headers.get('retry-after');\n        throw error;\n      }\n      return response;\n    } catch (error) {\n      lastError = error;\n      if (attempt === MAX_ATTEMPTS || !shouldRetry(error)) break;\n      const wait = parseRetryAfter(error.retryAfter);\n      await sleep(wait === null ? DELAY_MS : wait);\n    }\n  }\n  throw lastError;\n}\n\nmodule.exports = { fetchWithRetry, shouldRetry, parseRetryAfter };\n",
)
write(
    "test/retry.test.js",
    "'use strict';\n\nconst test = require('node:test');\nconst assert = require('node:assert');\nconst { fetchWithRetry, parseRetryAfter } = require('../src/retry');\n\nfunction fakeFetch(statuses) {\n  const calls = [];\n  const impl = async (url) => {\n    calls.push(url);\n    const status = statuses[Math.min(calls.length - 1, statuses.length - 1)];\n    return { ok: status < 400, status };\n  };\n  return { impl, calls };\n}\n\ntest('returns the first successful response', async () => {\n  const { impl, calls } = fakeFetch([503, 200]);\n  const response = await fetchWithRetry('https://example.test', {}, impl);\n  assert.strictEqual(response.status, 200);\n  assert.strictEqual(calls.length, 2);\n});\n\ntest('gives up after three attempts', async () => {\n  const { impl, calls } = fakeFetch([503]);\n  await assert.rejects(fetchWithRetry('https://example.test', {}, impl), /HTTP 503/);\n  assert.strictEqual(calls.length, 3);\n});\n\ntest('reads Retry-After seconds', () => {\n  assert.strictEqual(parseRetryAfter('3'), 3);\n  assert.strictEqual(parseRetryAfter(undefined), null);\n});\n\ntest('retries after a Retry-After response', async () => {\n  const calls = [];\n  const impl = async (url) => {\n    calls.push(url);\n    const status = calls.length === 1 ? 503 : 200;\n    return { ok: status < 400, status, headers: { get: () => '0' } };\n  };\n  const response = await fetchWithRetry('https://example.test', {}, impl);\n  assert.strictEqual(response.status, 200);\n});\n",
)
git("add", "-A")
git("commit", "-q", "-m", "feat(retry): wait as long as Retry-After asks before retrying")
write(
    ".claude/workspace/issue-44/feature--issue-44/1.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\nNone found\n\n### Minor Issues\n1. **The README does not mention Retry-After** -- `README.md:3`. Add a sentence.\n\n### Summary\nOne Minor finding.\n\nAnswer: fixed in the round-1 commit.\n",
)
write(
    ".claude/workspace/issue-44/feature--issue-44/2.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\nNone found\n\n### Minor Issues\n1. **The test names do not say what they check** -- `README.md:3`. Add a sentence.\n\n### Summary\nOne Minor finding.\n\nAnswer: fixed in the round-2 commit.\n",
)
write(
    ".claude/workspace/issue-44/feature--issue-44/cycle.md",
    "# Review cycle: feature/issue-44\n\nMode: raise\nBase: main\nRound: 2 (addressed)\nClean rounds in a row: 0\nRaised findings: none\nPR: none\n",
)
write(
    ".claude/workspace/issue-44/feature--issue-44/pr.md",
    "feat(retry): wait as long as Retry-After asks before retrying\n\nHonour Retry-After when retrying.\n\nCloses #44\n",
)
