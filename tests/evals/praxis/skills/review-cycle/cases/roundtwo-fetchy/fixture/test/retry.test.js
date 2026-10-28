'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { fetchWithRetry, parseRetryAfter } = require('../src/retry');

function fakeFetch(statuses) {
  const calls = [];
  const impl = async (url) => {
    calls.push(url);
    const status = statuses[Math.min(calls.length - 1, statuses.length - 1)];
    return { ok: status < 400, status };
  };
  return { impl, calls };
}

test('returns the first successful response', async () => {
  const { impl, calls } = fakeFetch([503, 200]);
  const response = await fetchWithRetry('https://example.test', {}, impl);
  assert.strictEqual(response.status, 200);
  assert.strictEqual(calls.length, 2);
});

test('gives up after three attempts', async () => {
  const { impl, calls } = fakeFetch([503]);
  await assert.rejects(fetchWithRetry('https://example.test', {}, impl), /HTTP 503/);
  assert.strictEqual(calls.length, 3);
});

test('reads Retry-After seconds', () => {
  assert.strictEqual(parseRetryAfter('3'), 3);
  assert.strictEqual(parseRetryAfter(undefined), null);
});
