const fs = require("node:fs");
const { wrap } = require("./wrap");

// rewrap [--width N]: wrap stdin to N characters a line.
function main(argv) {
  const i = argv.indexOf("--width");
  const width = i === -1 ? 72 : Number(argv[i + 1]);
  const text = fs.readFileSync(0, "utf8");
  for (const line of wrap(text, width)) console.log(line);
}

module.exports = { main };
