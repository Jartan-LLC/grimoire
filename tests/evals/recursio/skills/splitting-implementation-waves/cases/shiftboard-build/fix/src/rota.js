import { formatDay, parseDay, parseStamp } from "./model.js";

const KINDS = ["times", "unknown", "role", "length", "overlap", "rest", "weekly"];

function mondayOf(start) {
  const day = Math.floor(parseStamp(start) / 1440);
  return day - ((day + 3) % 7); // 1970-01-01 was a Thursday
}

export function check(shifts, employees) {
  const byId = new Map(employees.map((e) => [e.id, e]));
  const problems = [];
  const add = (shift, kind, detail) => problems.push({ shift, kind, detail });
  const valid = [];
  shifts.forEach((s, i) => {
    const start = parseStamp(s.start);
    const end = parseStamp(s.end);
    if (end <= start) return add(i, "times", `${s.end} is not after ${s.start}`);
    const who = byId.get(s.employee);
    if (!who) return add(i, "unknown", `no employee ${s.employee}`);
    if (s.role !== who.role) add(i, "role", `${who.role} on a ${s.role} shift`);
    if (end - start > 720) add(i, "length", `${((end - start) / 60).toFixed(1)} h`);
    valid.push({ i, s, start, end });
  });
  const byEmployee = new Map();
  for (const v of valid) {
    if (!byEmployee.has(v.s.employee)) byEmployee.set(v.s.employee, []);
    byEmployee.get(v.s.employee).push(v);
  }
  for (const list of byEmployee.values()) {
    list.sort((a, b) => a.start - b.start || a.i - b.i);
    const weeks = new Map();
    list.forEach((v, k) => {
      const prev = list[k - 1];
      if (prev && v.start < prev.end) add(v.i, "overlap", `starts before shift ${prev.i + 1} ends`);
      else if (prev && v.start - prev.end < 660) add(v.i, "rest", `rest of ${((v.start - prev.end) / 60).toFixed(1)} h`);
      const monday = mondayOf(v.s.start);
      const week = weeks.get(monday) ?? { minutes: 0, flagged: false };
      week.minutes += v.end - v.start;
      if (!week.flagged && week.minutes > 48 * 60) {
        week.flagged = true;
        add(v.i, "weekly", `${(week.minutes / 60).toFixed(1)} h in the week of ${formatDay(monday)}`);
      }
      weeks.set(monday, week);
    });
  }
  return problems.sort((a, b) => a.shift - b.shift || KINDS.indexOf(a.kind) - KINDS.indexOf(b.kind));
}

export function cover(shifts, day, needs) {
  const base = parseDay(day) * 1440;
  const out = [];
  for (let hour = 0; hour < 24; hour++) {
    const from = base + hour * 60;
    for (const role of Object.keys(needs).sort()) {
      const have = shifts.filter((s) => s.role === role && parseStamp(s.start) <= from && parseStamp(s.end) >= from + 60).length;
      if (have < needs[role]) out.push({ hour, role, have, need: needs[role] });
    }
  }
  return out;
}
