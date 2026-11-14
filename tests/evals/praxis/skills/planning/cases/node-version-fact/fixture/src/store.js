const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const FILE = path.join(os.homedir(), '.todo.json');

function load() {
  return fs.existsSync(FILE) ? JSON.parse(fs.readFileSync(FILE, 'utf8')) : [];
}

module.exports = { load };
