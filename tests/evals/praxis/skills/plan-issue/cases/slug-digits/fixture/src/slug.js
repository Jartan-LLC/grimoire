// The slug of a post title: lowercase words joined by hyphens, accents dropped.
function slugify(title) {
  return title
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

module.exports = { slugify };
