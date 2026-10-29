#!/usr/bin/env node
const commands = {
  build: require("../src/build"),
  serve: require("../src/serve"),
  check: require("../src/spell"),
};

const [name, ...rest] = process.argv.slice(2);
const command = commands[name];
if (!command) {
  console.error(`usage: pkgdoc <${Object.keys(commands).join("|")}>`);
  process.exit(2);
}
process.exitCode = command.run(rest) || 0;
