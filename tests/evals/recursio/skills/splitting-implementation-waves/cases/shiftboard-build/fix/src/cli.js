import { readFileSync } from "node:fs";

import { entitlement, taken } from "./leave.js";
import { RotaError, employee, leave, shift } from "./model.js";
import { payslip } from "./pay.js";
import { check } from "./rota.js";


function rows(path) {
  const [header, ...lines] = readFileSync(path, "utf8").split(/\r?\n/).filter((l) => l.trim());
  const names = header.split(",");
  return lines.map((line) => Object.fromEntries(line.split(",").map((v, i) => [names[i], v])));
}

function employees(path) {
  return rows(path).map((r) =>
    employee({
      id: r.id, name: r.name, role: r.role, contractHours: Number(r.contract_hours),
      hourlyCents: Number(r.hourly_cents), startDate: r.start_date,
    }),
  );
}

function options(args) {
  const named = {};
  const positional = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith("--")) named[args[i].slice(2)] = args[++i];
    else positional.push(args[i]);
  }
  return { named, positional };
}

function find(list, id) {
  const found = list.find((e) => e.id === id);
  if (!found) throw new RotaError(`no employee ${id}`);
  return found;
}

const money = (cents) => (cents / 100).toFixed(2);
const hours = (minutes) => (minutes / 60).toFixed(2);

export function main(argv, io = { out: process.stdout, err: process.stderr }) {
  const [command, ...rest] = argv;
  const { named, positional } = options(rest);
  const say = (line) => io.out.write(`${line}\n`);
  try {
    if (command === "check") {
      const problems = check(rows(positional[1]).map((r) => shift(r)), employees(positional[0]));
      for (const p of problems) say(`shift ${p.shift + 1}: ${p.kind}: ${p.detail}`);
      return problems.length ? 1 : 0;
    }
    if (command === "pay") {
      const who = find(employees(positional[0]), named.employee);
      const holidays = new Set(named.holidays ? readFileSync(named.holidays, "utf8").split(/\s+/).filter(Boolean) : []);
      const slip = payslip(rows(positional[1]).map((r) => shift(r)), who, named.from, named.to, holidays);
      say(`minutes ${slip.minutes}`);
      for (const name of ["gross", "overtime", "total"]) say(`${name} ${money(slip[name])}`);
      return 0;
    }
    if (command === "leave") {
      const who = find(employees(positional[0]), named.employee);
      const year = Number(named.year);
      const all = rows(positional[1]).map((r) => leave(r));
      const have = entitlement(who, year);
      const used = taken(all, who, year);
      say(`entitlement ${hours(have)}`);
      say(`taken ${hours(used)}`);
      say(`balance ${hours(have - used)}`);
      return 0;
    }
    throw new RotaError(`unknown command: ${command}`);
  } catch (error) {
    if (!(error instanceof RotaError) && error.code !== "ENOENT") throw error;
    io.err.write(`${error.message}\n`);
    return 2;
  }
}
