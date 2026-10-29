#!/usr/bin/env node
const { parseArgs } = require("node:util");
const { runSession } = require("../src/session");

const { values } = parseArgs({
  options: {
    minutes: { type: "string", short: "m", default: "25" },
    quiet: { type: "boolean", short: "q", default: false },
  },
});
runSession(Number(values.minutes), { bell: !values.quiet });
