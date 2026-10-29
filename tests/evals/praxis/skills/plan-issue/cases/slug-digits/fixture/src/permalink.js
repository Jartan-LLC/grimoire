const { slugify } = require("./slug");

// A post's path: /<year>/<month>/<slug>/, from its publish date in UTC.
function permalink(post) {
  const date = new Date(post.published);
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  return `/${year}/${month}/${slugify(post.title)}/`;
}

module.exports = { permalink };
