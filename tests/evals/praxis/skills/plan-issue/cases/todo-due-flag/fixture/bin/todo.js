#!/usr/bin/env node
const { parseArgs } = require("../src/args");
const commands = {
  add: require("../src/commands/add"),
  list: require("../src/commands/list"),
  done: require("../src/commands/done"),
};

const args = parseArgs(process.argv.slice(2));
const command = commands[args.command];
if (!command) {
  console.error(`usage: todo <${Object.keys(commands).join("|")}> ...`);
  process.exit(2);
}
command.run(args);
