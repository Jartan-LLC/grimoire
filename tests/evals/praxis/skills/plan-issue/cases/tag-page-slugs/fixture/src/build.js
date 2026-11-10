// npm run build: write every post page and the index into public/.

const fs = require("node:fs");
const path = require("node:path");
const { readPosts, postPath } = require("./posts");
const { postPage, indexPage } = require("./html");

function writePage(out, address, html) {
  const dir = path.join(out, address);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "index.html"), html);
}

function build(postsDir, out) {
  const posts = readPosts(postsDir);
  for (const post of posts) {
    writePage(out, postPath(post), postPage(post));
  }
  writePage(out, "/", indexPage(posts, postPath));
}

if (require.main === module) {
  build(path.join(__dirname, "..", "posts"), path.join(__dirname, "..", "public"));
}

module.exports = { build };
