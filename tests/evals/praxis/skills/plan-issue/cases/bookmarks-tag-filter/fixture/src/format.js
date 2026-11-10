// One bookmark as `marks list` prints it: "  3 https://example.com [reading, rust]".
function formatBookmark(n, mark) {
  const tags = mark.tags.length ? ` [${mark.tags.join(", ")}]` : "";
  return `${String(n).padStart(3)} ${mark.url}${tags}`;
}

module.exports = { formatBookmark };
