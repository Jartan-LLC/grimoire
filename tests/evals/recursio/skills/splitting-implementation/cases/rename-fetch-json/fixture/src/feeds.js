import { fetchJson } from "./http.js";

/**
 * The titles of the newest `count` items of a JSON Feed.
 * @param {string} feedUrl
 * @param {number} [count]
 */
export async function latestTitles(feedUrl, count = 5) {
  const feed = await fetchJson(feedUrl, { headers: { accept: "application/feed+json" } });
  return feed.items.slice(0, count).map((item) => item.title ?? "(untitled)");
}
