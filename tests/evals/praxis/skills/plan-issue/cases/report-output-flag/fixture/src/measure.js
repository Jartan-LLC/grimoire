const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");

// Every file under `dir`, with its raw and gzipped size in bytes, largest gzipped first.
function measure(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { recursive: true, withFileTypes: true })) {
    if (!entry.isFile()) continue;
    const full = path.join(entry.parentPath, entry.name);
    const data = fs.readFileSync(full);
    files.push({ file: path.relative(dir, full), raw: data.length, gzip: zlib.gzipSync(data).length });
  }
  return files.sort((a, b) => b.gzip - a.gzip);
}

// "50kb" -> 51200, "1mb" -> 1048576, "900" -> 900.
function parseSize(text) {
  const match = /^(\d+(?:\.\d+)?)\s*(kb|mb)?$/i.exec(text.trim());
  if (!match) throw new Error(`not a size: ${text}`);
  const unit = { kb: 1024, mb: 1024 * 1024 }[(match[2] || "").toLowerCase()] || 1;
  return Math.round(Number(match[1]) * unit);
}

module.exports = { measure, parseSize };
