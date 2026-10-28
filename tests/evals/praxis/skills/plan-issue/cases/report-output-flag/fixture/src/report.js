const fs = require("node:fs");
const { execFile } = require("node:child_process");

function table(files, budget) {
  return files
    .map((f) => `${f.gzip > budget ? "OVER" : "  ok"}  ${String(f.gzip).padStart(8)}  ${f.file}`)
    .join("\n");
}

function json(files, budget) {
  return JSON.stringify({ budget: Number.isFinite(budget) ? budget : null, files }, null, 2);
}

// Writes sizecheck-report.html in the current folder and opens it in the default browser.
function openHtml(files) {
  const rows = files.map((f) => `<tr><td>${f.file}</td><td>${f.gzip}</td></tr>`).join("");
  fs.writeFileSync("sizecheck-report.html", `<table>${rows}</table>`);
  const opener = process.platform === "darwin" ? "open" : "xdg-open";
  execFile(opener, ["sizecheck-report.html"], () => {});
}

module.exports = { table, json, openHtml };
