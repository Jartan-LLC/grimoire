const store = require("../store");

function formatItem(item) {
  const box = item.done ? "[x]" : "[ ]";
  const tag = item.tag ? ` #${item.tag}` : "";
  return `${String(item.id).padStart(3)} ${box} ${item.text}${tag}`;
}

function run(args) {
  const items = store.load().filter((item) => args.all || !item.done);
  for (const item of items) console.log(formatItem(item));
}

module.exports = { formatItem, run };
