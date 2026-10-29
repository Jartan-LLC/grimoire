const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const FILE = process.env.TODO_FILE || path.join(os.homedir(), ".todo.json");

function load() {
  if (!fs.existsSync(FILE)) return [];
  return JSON.parse(fs.readFileSync(FILE, "utf8"));
}

function save(items) {
  fs.writeFileSync(FILE, JSON.stringify(items, null, 2));
}

module.exports = { load, save };
