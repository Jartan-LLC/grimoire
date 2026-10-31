// SPDX-License-Identifier: BSD-3-Clause
// Format byte counts for people.

const UNITS = ['B', 'KiB', 'MiB', 'GiB', 'TiB'];

export type Options = { precision?: number };

export function formatSize(bytes: number, options: Options = {}): string {
  const precision = options.precision ?? 1;
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < UNITS.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return unit === 0 ? `${bytes} B` : `${value.toFixed(precision)} ${UNITS[unit]}`;
}
