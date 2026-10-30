const UNITS = ["B", "KiB", "MiB", "GiB"];

/**
 * A byte count for the job report: one decimal above bytes, e.g. `1.5 KiB`.
 * @param {number} bytes
 */
export function formatBytes(bytes) {
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return unit === 0 ? `${value} B` : `${value.toFixed(1)} ${UNITS[unit]}`;
}
