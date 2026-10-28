'use strict';

const DELAY_MS = 100;
const MAX_ATTEMPTS = 3;

// Whether a failed attempt is worth another try: any error, for now.
function shouldRetry(error) {
  return Boolean(error);
}

// Seconds from a Retry-After header, or null when it is missing or not a number.
function parseRetryAfter(value) {
  const seconds = Number(value);
  return Number.isFinite(seconds) ? seconds : null;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithRetry(url, options = {}, fetchImpl = globalThis.fetch) {
  let lastError;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    try {
      const response = await fetchImpl(url, options);
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}`);
        error.status = response.status;
        throw error;
      }
      return response;
    } catch (error) {
      lastError = error;
      if (attempt === MAX_ATTEMPTS || !shouldRetry(error)) break;
      await sleep(DELAY_MS);
    }
  }
  throw lastError;
}

module.exports = { fetchWithRetry, shouldRetry, parseRetryAfter };
