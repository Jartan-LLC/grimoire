// The notes as plain text, for the release email.
function renderText(release) {
  const lines = [`Release ${release.version} (${release.date})`];
  for (const section of release.sections) {
    lines.push("", `${section.title}:`, ...section.items.map((item) => `  - ${item}`));
  }
  return lines.join("\n");
}

module.exports = { renderText };
