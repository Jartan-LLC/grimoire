// SPDX-License-Identifier: BSD-3-Clause
// Format byte counts for people.

const BINARY = ['B', 'KiB', 'MiB', 'GiB', 'TiB'];
const SI = ['B', 'kB', 'MB', 'GB', 'TB'];

export type Options = { precision?: number; si?: boolean };

export function formatSize(bytes: number, options: Options = {}): string {
  const precision = options.precision ?? 1;
  const base = options.si ? 1000 : 1024;
  const units = options.si ? SI : BINARY;
  let value = bytes;
  let unit = 0;
  while (value >= base && unit < units.length - 1) {
    value /= base;
    unit += 1;
  }
  return unit === 0 ? `${bytes} B` : `${value.toFixed(precision)} ${units[unit]}`;
}
