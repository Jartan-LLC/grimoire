const fs = require("node:fs");

const SECTIONS = { added: "Added", changed: "Changed", fixed: "Fixed" };

// The release for `version`, its changes grouped by section in SECTIONS order.
function findRelease(file, version) {
  const release = JSON.parse(fs.readFileSync(file, "utf8")).find((r) => r.version === version);
  if (!release) throw new Error(`no release ${version} in ${file}`);
  const sections = Object.entries(SECTIONS)
    .map(([type, title]) => ({ title, items: release.changes.filter((c) => c.type === type).map((c) => c.text) }))
    .filter((s) => s.items.length);
  return { version: release.version, date: release.date, sections };
}

module.exports = { findRelease };
