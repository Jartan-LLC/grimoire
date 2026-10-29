const store = require("../store");

function run(args) {
  const id = Number(args.positional[0]);
  const items = store.load().map((item) => (item.id === id ? { ...item, done: true } : item));
  store.save(items);
}

module.exports = { run };
