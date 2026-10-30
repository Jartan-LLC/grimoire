const fs = require("node:fs");

// An event: { id, title, start, end, tags }, with start and end as ISO 8601 strings.
function loadEvents(path) {
  const events = JSON.parse(fs.readFileSync(path, "utf8"));
  return events.sort((a, b) => a.start.localeCompare(b.start));
}

module.exports = { loadEvents };
