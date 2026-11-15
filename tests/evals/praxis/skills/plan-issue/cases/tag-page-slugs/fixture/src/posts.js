// Read the posts and work out their addresses.

const fs = require("node:fs");
const path = require("node:path");

// A title as a lowercase, ASCII-only address part: "Cafe con leche: notes" -> "cafe-con-leche-notes".
function slugify(title) {
  return title
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function parsePost(text) {
  const [, head, body] = text.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  const fields = Object.fromEntries(
    head.split("\n").map((line) => {
      const at = line.indexOf(":");
      return [line.slice(0, at).trim(), line.slice(at + 1).trim()];
    }),
  );
  const tags = fields.tags ? fields.tags.split(",").map((tag) => tag.trim()) : [];
  return { title: fields.title, date: fields.date, tags, body: body.trim() };
}

function readPosts(dir) {
  return fs
    .readdirSync(dir)
    .filter((name) => name.endsWith(".md"))
    .map((name) => parsePost(fs.readFileSync(path.join(dir, name), "utf8")))
    .sort((a, b) => b.date.localeCompare(a.date));
}

function postPath(post) {
  return `/posts/${slugify(post.title)}/`;
}

module.exports = { parsePost, readPosts, postPath };
