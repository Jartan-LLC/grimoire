#!/usr/bin/env node
const fs = require("node:fs");
const { parseArgs } = require("node:util");
const { format } = require("../src/format");

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    "in-place": { type: "boolean", short: "i" },
    check: { type: "boolean" },
    sort: { type: "boolean", short: "s" },
  },
});

for (const file of positionals) {
  const text = fs.readFileSync(file, "utf8");
  const out = format(text, { sort: values.sort });
  if (values.check) {
    if (out !== text) {
      console.error(`${file}: not formatted`);
      process.exitCode = 1;
    }
  } else if (values["in-place"]) {
    fs.writeFileSync(file, out);
  } else {
    process.stdout.write(out);
  }
}
