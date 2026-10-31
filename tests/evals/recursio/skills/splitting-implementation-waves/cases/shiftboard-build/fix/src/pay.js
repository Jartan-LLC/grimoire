import { formatDay, parseDay, parseStamp } from "./model.js";

export const PREMIUMS = Object.freeze({ night: 25, weekend: 50, holiday: 100 });

function percentAt(minute, holidays) {
  const day = Math.floor(minute / 1440);
  const clock = minute % 1440;
  const weekday = (day + 4) % 7; // 0 Sunday, 6 Saturday
  if (holidays.has(formatDay(day))) return PREMIUMS.holiday;
  if (weekday === 0 || weekday === 6) return PREMIUMS.weekend;
  if (clock >= 22 * 60 || clock < 6 * 60) return PREMIUMS.night;
  return 0;
}

function roundCents(numerator, denominator) {
  return Math.floor((2 * numerator + denominator) / (2 * denominator));
}

export function shiftPay(shift, employee, holidays = new Set()) {
  const start = parseStamp(shift.start);
  const end = parseStamp(shift.end);
  let percentMinutes = 0;
  for (let m = start; m < end; m++) percentMinutes += 100 + percentAt(m, holidays);
  return roundCents(percentMinutes * employee.hourlyCents, 6000);
}

function mondayOf(stamp) {
  const day = Math.floor(parseStamp(stamp) / 1440);
  return day - ((day + 3) % 7);
}

export function overtime(shifts, employee) {
  const weeks = new Map();
  for (const s of shifts.filter((x) => x.employee === employee.id)) {
    const monday = mondayOf(s.start);
    weeks.set(monday, (weeks.get(monday) ?? 0) + parseStamp(s.end) - parseStamp(s.start));
  }
  let cents = 0;
  for (const minutes of weeks.values()) {
    const over = minutes - employee.contractHours * 60;
    if (over > 0) cents += roundCents(over * employee.hourlyCents, 120);
  }
  return cents;
}

export function payslip(shifts, employee, from, to, holidays = new Set()) {
  const first = parseDay(from);
  const last = parseDay(to);
  const mine = shifts.filter((s) => {
    const day = Math.floor(parseStamp(s.start) / 1440);
    return s.employee === employee.id && day >= first && day <= last;
  });
  const minutes = mine.reduce((sum, s) => sum + parseStamp(s.end) - parseStamp(s.start), 0);
  const gross = mine.reduce((sum, s) => sum + shiftPay(s, employee, holidays), 0);
  const extra = overtime(mine, employee);
  return { minutes, gross, overtime: extra, total: gross + extra };
}
