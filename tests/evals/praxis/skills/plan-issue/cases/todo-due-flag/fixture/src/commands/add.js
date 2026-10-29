const store = require("../store");

function addItem(items, text, tag) {
  const id = items.length ? Math.max(...items.map((item) => item.id)) + 1 : 1;
  return [...items, { id, text, tag, done: false }];
}

function run(args) {
  const text = args.positional.join(" ");
  if (!text) {
    console.error('usage: todo add "text" [--tag name]');
    process.exit(2);
  }
  store.save(addItem(store.load(), text, args.tag));
}

module.exports = { addItem, run };
