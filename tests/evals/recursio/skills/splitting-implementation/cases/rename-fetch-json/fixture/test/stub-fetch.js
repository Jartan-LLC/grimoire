/**
 * Replaces the global fetch with one that answers every request from `answer(url)`, and records
 * the URLs asked for. Call the returned `restore` when the test is done.
 * @param {(url: string) => Response} answer
 */
export function stubFetch(answer) {
  const original = globalThis.fetch;
  const urls = [];
  globalThis.fetch = async (url) => {
    urls.push(String(url));
    return answer(String(url));
  };
  return { urls, restore: () => (globalThis.fetch = original) };
}

/** @param {unknown} body */
export function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}
