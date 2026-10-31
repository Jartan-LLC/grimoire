import { parseDate, slugify, truncate, uniqueBy } from "./helpers.js";

/**
 * @typedef {{ title: string, date: Date, slug: string, summary: string, body: string }} Post
 */

/**
 * A post from its front matter and body.
 * @param {{ title: string, date: string, slug?: string }} meta
 * @param {string} body
 * @returns {Post}
 */
export function makePost(meta, body) {
  return {
    title: meta.title,
    date: parseDate(meta.date),
    slug: meta.slug ?? slugify(meta.title),
    summary: truncate(body.split("\n\n")[0], 160),
    body,
  };
}

/**
 * The newest posts first, one per slug.
 * @param {Post[]} posts
 */
export function frontPage(posts) {
  return uniqueBy([...posts].sort((a, b) => b.date.getTime() - a.date.getTime()), (post) => post.slug);
}
