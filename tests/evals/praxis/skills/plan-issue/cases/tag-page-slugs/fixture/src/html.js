// The page templates.

function escape(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function postPage(post) {
  const tags = post.tags.map((tag) => `<li>${escape(tag)}</li>`).join("");
  return `<article><h1>${escape(post.title)}</h1><p>${escape(post.body)}</p><ul class="tags">${tags}</ul></article>`;
}

function indexPage(posts, pathOf) {
  const items = posts.map((post) => `<li><a href="${pathOf(post)}">${escape(post.title)}</a></li>`);
  return `<ul>${items.join("")}</ul>`;
}

module.exports = { escape, postPage, indexPage };
