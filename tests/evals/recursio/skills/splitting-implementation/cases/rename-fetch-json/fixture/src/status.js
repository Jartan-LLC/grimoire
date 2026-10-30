import { HttpError, fetchJson } from "./http.js";

/**
 * Whether a service's health endpoint says it is up. An HTTP error counts as down.
 * @param {string} baseUrl
 */
export async function isUp(baseUrl) {
  try {
    const health = await fetchJson(`${baseUrl}/health`, { timeoutMs: 3000 });
    return health?.status === "ok";
  } catch (error) {
    if (error instanceof HttpError) return false;
    throw error;
  }
}
