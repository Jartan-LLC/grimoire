import { chunk, groupBy, monthKey, titleCase } from "./helpers.js";

/**
 * The archive's pages: posts grouped by month, newest month first, `perPage` posts a page.
 * @param {import("./posts.js").Post[]} posts
 * @param {number} perPage
 */
export function archivePages(posts, perPage) {
  const months = [...groupBy(posts, (post) => monthKey(post.date)).entries()].sort((a, b) =>
    b[0].localeCompare(a[0]),
  );
  return months.flatMap(([month, items]) =>
    chunk(items, perPage).map((page, i) => ({ month, page: i + 1, titles: page.map((p) => titleCase(p.title)) })),
  );
}
