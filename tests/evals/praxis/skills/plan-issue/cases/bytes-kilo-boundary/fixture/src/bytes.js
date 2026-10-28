const UNITS = ["B", "KB", "MB", "GB", "TB"];

// Binary steps (1 KB = 1024 B), one decimal place above bytes.
function formatBytes(bytes) {
  let value = bytes;
  let unit = 0;
  while (value > 1024 && unit < UNITS.length - 1) {
    value /= 1024;
    unit++;
  }
  return unit === 0 ? `${value} B` : `${value.toFixed(1)} ${UNITS[unit]}`;
}

module.exports = { formatBytes };
