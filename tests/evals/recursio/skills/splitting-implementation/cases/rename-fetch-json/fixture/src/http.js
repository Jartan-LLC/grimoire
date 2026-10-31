/** A non-2xx answer, with its status and the body text. */
export class HttpError extends Error {
  /**
   * @param {string} url
   * @param {number} status
   * @param {string} body
   */
  constructor(url, status, body) {
    super(`${url}: HTTP ${status}`);
    this.name = "HttpError";
    this.status = status;
    this.body = body;
  }
}

/**
 * GETs `url` and parses the body as JSON. A non-2xx answer throws HttpError; a 204 gives null.
 * @param {string} url
 * @param {{ headers?: Record<string, string>, timeoutMs?: number }} [options]
 */
export async function fetchJson(url, { headers = {}, timeoutMs = 10000 } = {}) {
  const response = await fetch(url, {
    headers: { accept: "application/json", ...headers },
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (!response.ok) throw new HttpError(url, response.status, await response.text());
  if (response.status === 204) return null;
  return response.json();
}
