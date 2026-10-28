"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("checkout", "-q", "-b", "feature/issue-52")
write(
    "src/retry.js",
    "'use strict';\n\nconst DELAY_MS = 100;\nconst MAX_ATTEMPTS = 3;\n\n// Whether a failed attempt is worth another try: a server error, never a client error.\nfunction shouldRetry(error) {\n  return error.status >= 500;\n}\n\n// Seconds from a Retry-After header, or null when it is missing or not a number.\nfunction parseRetryAfter(value) {\n  const seconds = Number(value);\n  return Number.isFinite(seconds) ? seconds : null;\n}\n\nfunction sleep(ms) {\n  return new Promise((resolve) => setTimeout(resolve, ms));\n}\n\nasync function fetchWithRetry(url, options = {}, fetchImpl = globalThis.fetch) {\n  let lastError;\n  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {\n    try {\n      const response = await fetchImpl(url, options);\n      if (!response.ok) {\n        const error = new Error(`HTTP ${response.status}`);\n        error.status = response.status;\n        throw error;\n      }\n      return response;\n    } catch (error) {\n      lastError = error;\n      if (attempt === MAX_ATTEMPTS || !shouldRetry(error)) break;\n      await sleep(DELAY_MS);\n    }\n  }\n  throw lastError;\n}\n\nmodule.exports = { fetchWithRetry, shouldRetry, parseRetryAfter };\n",
)
write(
    "test/retry.test.js",
    "'use strict';\n\nconst test = require('node:test');\nconst assert = require('node:assert');\nconst { fetchWithRetry, parseRetryAfter } = require('../src/retry');\n\nfunction fakeFetch(statuses) {\n  const calls = [];\n  const impl = async (url) => {\n    calls.push(url);\n    const status = statuses[Math.min(calls.length - 1, statuses.length - 1)];\n    return { ok: status < 400, status };\n  };\n  return { impl, calls };\n}\n\ntest('returns the first successful response', async () => {\n  const { impl, calls } = fakeFetch([503, 200]);\n  const response = await fetchWithRetry('https://example.test', {}, impl);\n  assert.strictEqual(response.status, 200);\n  assert.strictEqual(calls.length, 2);\n});\n\ntest('gives up after three attempts', async () => {\n  const { impl, calls } = fakeFetch([503]);\n  await assert.rejects(fetchWithRetry('https://example.test', {}, impl), /HTTP 503/);\n  assert.strictEqual(calls.length, 3);\n});\n\ntest('reads Retry-After seconds', () => {\n  assert.strictEqual(parseRetryAfter('3'), 3);\n  assert.strictEqual(parseRetryAfter(undefined), null);\n});\n\ntest('client error', async () => {\n  const { impl, calls } = fakeFetch([404]);\n  await assert.rejects(fetchWithRetry('https://example.test', {}, impl), /HTTP 404/);\n  assert.strictEqual(calls.length, 1);\n});\n",
)
git("add", "-A")
git("commit", "-q", "-m", "fix(retry): stop retrying client errors")
write(
    "src/retry.js",
    "'use strict';\n\nconst DELAY_MS = 100;\nconst MAX_ATTEMPTS = 3;\n\n// Whether a failed attempt is worth another try: a network or server error, never a client error.\nfunction shouldRetry(error) {\n  if (error.status === undefined) return true;\n  return error.status >= 500;\n}\n\n// Seconds from a Retry-After header, or null when it is missing or not a number.\nfunction parseRetryAfter(value) {\n  const seconds = Number(value);\n  return Number.isFinite(seconds) ? seconds : null;\n}\n\nfunction sleep(ms) {\n  return new Promise((resolve) => setTimeout(resolve, ms));\n}\n\nasync function fetchWithRetry(url, options = {}, fetchImpl = globalThis.fetch) {\n  let lastError;\n  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {\n    try {\n      const response = await fetchImpl(url, options);\n      if (!response.ok) {\n        const error = new Error(`HTTP ${response.status}`);\n        error.status = response.status;\n        throw error;\n      }\n      return response;\n    } catch (error) {\n      lastError = error;\n      if (attempt === MAX_ATTEMPTS || !shouldRetry(error)) break;\n      await sleep(DELAY_MS);\n    }\n  }\n  throw lastError;\n}\n\nmodule.exports = { fetchWithRetry, shouldRetry, parseRetryAfter };\n",
)
write(
    "test/retry.test.js",
    "'use strict';\n\nconst test = require('node:test');\nconst assert = require('node:assert');\nconst { fetchWithRetry, parseRetryAfter } = require('../src/retry');\n\nfunction fakeFetch(statuses) {\n  const calls = [];\n  const impl = async (url) => {\n    calls.push(url);\n    const status = statuses[Math.min(calls.length - 1, statuses.length - 1)];\n    return { ok: status < 400, status };\n  };\n  return { impl, calls };\n}\n\ntest('returns the first successful response', async () => {\n  const { impl, calls } = fakeFetch([503, 200]);\n  const response = await fetchWithRetry('https://example.test', {}, impl);\n  assert.strictEqual(response.status, 200);\n  assert.strictEqual(calls.length, 2);\n});\n\ntest('gives up after three attempts', async () => {\n  const { impl, calls } = fakeFetch([503]);\n  await assert.rejects(fetchWithRetry('https://example.test', {}, impl), /HTTP 503/);\n  assert.strictEqual(calls.length, 3);\n});\n\ntest('reads Retry-After seconds', () => {\n  assert.strictEqual(parseRetryAfter('3'), 3);\n  assert.strictEqual(parseRetryAfter(undefined), null);\n});\n\ntest('client error', async () => {\n  const { impl, calls } = fakeFetch([404]);\n  await assert.rejects(fetchWithRetry('https://example.test', {}, impl), /HTTP 404/);\n  assert.strictEqual(calls.length, 1);\n});\n\ntest('network error', async () => {\n  const calls = [];\n  const impl = async (url) => {\n    calls.push(url);\n    if (calls.length === 1) throw new TypeError('fetch failed');\n    return { ok: true, status: 200 };\n  };\n  const response = await fetchWithRetry('https://example.test', {}, impl);\n  assert.strictEqual(response.status, 200);\n  assert.strictEqual(calls.length, 2);\n});\n",
)
write(
    "README.md",
    "# fetchy\n\n`fetchWithRetry(url, options)` calls `fetch` and retries a failed request, up to three attempts in all. A client error (4xx) is not retried.\n\n## Development\n\nRun the tests with `npm test`.\n",
)
git("add", "-A")
git(
    "commit",
    "-q",
    "-m",
    "fix(retry): retry network errors again",
    "-m",
    "An error thrown by fetch itself has no status, and undefined >= 500 is false, so a dropped connection failed on the first attempt. The README now says client errors are not retried.",
)
write(
    "test/retry.test.js",
    "'use strict';\n\nconst test = require('node:test');\nconst assert = require('node:assert');\nconst { fetchWithRetry, parseRetryAfter } = require('../src/retry');\n\nfunction fakeFetch(statuses) {\n  const calls = [];\n  const impl = async (url) => {\n    calls.push(url);\n    const status = statuses[Math.min(calls.length - 1, statuses.length - 1)];\n    return { ok: status < 400, status };\n  };\n  return { impl, calls };\n}\n\ntest('returns the first successful response', async () => {\n  const { impl, calls } = fakeFetch([503, 200]);\n  const response = await fetchWithRetry('https://example.test', {}, impl);\n  assert.strictEqual(response.status, 200);\n  assert.strictEqual(calls.length, 2);\n});\n\ntest('gives up after three attempts', async () => {\n  const { impl, calls } = fakeFetch([503]);\n  await assert.rejects(fetchWithRetry('https://example.test', {}, impl), /HTTP 503/);\n  assert.strictEqual(calls.length, 3);\n});\n\ntest('reads Retry-After seconds', () => {\n  assert.strictEqual(parseRetryAfter('3'), 3);\n  assert.strictEqual(parseRetryAfter(undefined), null);\n});\n\ntest('gives up at once on a client error', async () => {\n  const { impl, calls } = fakeFetch([404]);\n  await assert.rejects(fetchWithRetry('https://example.test', {}, impl), /HTTP 404/);\n  assert.strictEqual(calls.length, 1);\n});\n\ntest('retries after a network error', async () => {\n  const calls = [];\n  const impl = async (url) => {\n    calls.push(url);\n    if (calls.length === 1) throw new TypeError('fetch failed');\n    return { ok: true, status: 200 };\n  };\n  const response = await fetchWithRetry('https://example.test', {}, impl);\n  assert.strictEqual(response.status, 200);\n  assert.strictEqual(calls.length, 2);\n});\n",
)
git("add", "-A")
git("commit", "-q", "-m", "test(retry): name the client and network error tests")
write(
    ".claude/workspace/issue-52/feature--issue-52/1.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\n1. **A network error is no longer retried** -- `src/retry.js:8`. An error thrown by `fetch` itself has no `status`, and `undefined >= 500` is false, so a dropped connection now fails on the first attempt.\n\nAnswer: fixed in the round-1 commit.\n\n### Minor Issues\n1. **The README does not say client errors are not retried** -- `README.md:3`. Add a sentence.\n\nAnswer: fixed in the round-1 commit.\n\n### Summary\nOne Important and one Minor finding.\n",
)
write(
    ".claude/workspace/issue-52/feature--issue-52/2.md",
    "## Code Review\n\n### Critical Issues\nNone found\n\n### Important Issues\nNone found\n\n### Minor Issues\n1. **The test names do not say what they check** -- `test/retry.test.js:35`. `client error` and `network error` name the input, not what each test expects.\n\nAnswer: fixed in the round-2 commit.\n\n### Summary\nOne Minor finding.\n",
)
write(
    ".claude/workspace/issue-52/feature--issue-52/cycle.md",
    "# Review cycle: feature/issue-52\n\nMode: decide\nBase: main\nRound: 2 (addressed)\nClean rounds in a row: 1\nRaised findings: none\nDecided findings: none\nPR: none\n",
)
write(
    ".claude/workspace/issue-52/feature--issue-52/pr.md",
    "fix(retry): stop retrying client errors\n\nGive up at once on a client error, since retrying a 404 or a 400 cannot succeed.\n\nCloses #52\n",
)
