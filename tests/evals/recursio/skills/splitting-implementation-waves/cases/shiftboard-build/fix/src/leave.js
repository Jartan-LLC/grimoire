import { LeaveKind, RotaError, parseDay } from "./model.js";

function yearBounds(year) {
  return [parseDay(`${year}-01-01`), parseDay(`${year}-12-31`)];
}

export function entitlement(employee, year) {
  const [first, last] = yearBounds(year);
  const start = parseDay(employee.startDate);
  if (start > last) return 0;
  const full = 5.6 * employee.contractHours * 60;
  if (start <= first) return Math.round(full);
  return Math.round((full * (last - start + 1)) / (last - first + 1));
}

function weekdays(from, to) {
  let n = 0;
  for (let d = from; d <= to; d++) {
    const weekday = (d + 4) % 7;
    if (weekday !== 0 && weekday !== 6) n++;
  }
  return n;
}

export function taken(leaves, employee, year) {
  const [first, last] = yearBounds(year);
  let days = 0;
  for (const l of leaves) {
    if (l.employee !== employee.id || l.kind !== LeaveKind.ANNUAL) continue;
    days += weekdays(Math.max(parseDay(l.from), first), Math.min(parseDay(l.to), last));
  }
  return days * employee.contractHours * 12;
}

export function request(leaves, employee, wanted, year) {
  const from = parseDay(wanted.from);
  const to = parseDay(wanted.to);
  if (to < from) throw new RotaError(`${wanted.to} is before ${wanted.from}`);
  if (wanted.employee !== employee.id) throw new RotaError(`leave for ${wanted.employee}, not ${employee.id}`);
  for (const l of leaves) {
    if (l.employee === employee.id && parseDay(l.from) <= to && parseDay(l.to) >= from) {
      throw new RotaError(`overlaps leave from ${l.from} to ${l.to}`);
    }
  }
  const next = [...leaves, wanted];
  if (wanted.kind === LeaveKind.ANNUAL && taken(next, employee, year) > entitlement(employee, year)) {
    throw new RotaError(`not enough annual leave left in ${year}`);
  }
  return next;
}

export function bradford(leaves, employee, today) {
  const last = parseDay(today);
  const first = last - 364;
  let spells = 0;
  let days = 0;
  for (const l of leaves) {
    if (l.employee !== employee.id || l.kind !== LeaveKind.SICK) continue;
    const from = Math.max(parseDay(l.from), first);
    const to = Math.min(parseDay(l.to), last);
    if (to < from) continue;
    spells++;
    days += to - from + 1;
  }
  return spells * spells * days;
}
