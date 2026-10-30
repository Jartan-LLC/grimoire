#!/usr/bin/env node
const { loadEvents } = require("../src/events");

const [command] = process.argv.slice(2);
if (command === "list") {
  for (const event of loadEvents("events.json")) {
    console.log(`${event.start}  ${event.title}`);
  }
} else {
  console.error("usage: eventlog list");
  process.exit(2);
}
