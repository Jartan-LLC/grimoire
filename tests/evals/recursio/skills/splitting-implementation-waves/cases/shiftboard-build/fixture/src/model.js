// The records the shiftboard modules pass to one another.

/** A request the rota refuses or input it cannot work with; the message says why. */
export class RotaError extends Error {
  constructor(message) {
    super(message);
    this.name = "RotaError";
  }
}

export const Role = Object.freeze({ NURSE: "nurse", CARER: "carer", COOK: "cook" });
export const LeaveKind = Object.freeze({ ANNUAL: "annual", SICK: "sick" });

const STAMP = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/;
const DAY = /^(\d{4})-(\d{2})-(\d{2})$/;

/** Minutes since 1970-01-01T00:00 of a `YYYY-MM-DDTHH:MM` wall-clock time; there are no time zones. */
export function parseStamp(text) {
  const m = STAMP.exec(text);
  if (!m) throw new RotaError(`not a time: ${text}`);
  const ms = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]);
  if (new Date(ms).toISOString().slice(0, 16) !== text) throw new RotaError(`not a time: ${text}`);
  return ms / 60000;
}

/** Days since 1970-01-01 of a `YYYY-MM-DD` date. */
export function parseDay(text) {
  const m = DAY.exec(text);
  if (!m) throw new RotaError(`not a date: ${text}`);
  const ms = Date.UTC(+m[1], +m[2] - 1, +m[3]);
  if (new Date(ms).toISOString().slice(0, 10) !== text) throw new RotaError(`not a date: ${text}`);
  return ms / 86400000;
}

/** The `YYYY-MM-DD` text of a day number from `parseDay`. */
export function formatDay(day) {
  return new Date(day * 86400000).toISOString().slice(0, 10);
}

function need(value, what) {
  if (value === undefined || value === null || value === "") throw new RotaError(`missing ${what}`);
  return value;
}

function oneOf(value, kinds, what) {
  if (!Object.values(kinds).includes(value)) throw new RotaError(`unknown ${what}: ${value}`);
  return value;
}

function whole(value, what) {
  if (!Number.isInteger(value) || value < 0) throw new RotaError(`${what} must be a whole number: ${value}`);
  return value;
}

/** A member of staff. `contractHours` a week; `hourlyCents` the base rate in cents; `startDate` `YYYY-MM-DD`. */
export function employee({ id, name, role, contractHours, hourlyCents, startDate }) {
  parseDay(need(startDate, "start date"));
  return Object.freeze({
    id: need(id, "employee id"),
    name: need(name, "name"),
    role: oneOf(role, Role, "role"),
    contractHours: whole(contractHours, "contract hours"),
    hourlyCents: whole(hourlyCents, "hourly rate"),
    startDate,
  });
}

/** One shift worked by `employee` (an id) in `role`, from `start` to `end`, both `YYYY-MM-DDTHH:MM`. */
export function shift({ employee: who, start, end, role }) {
  parseStamp(need(start, "start"));
  parseStamp(need(end, "end"));
  return Object.freeze({ employee: need(who, "employee"), start, end, role: oneOf(role, Role, "role") });
}

/** Leave of `kind` for `employee` (an id), `from` and `to` both `YYYY-MM-DD` and both included. */
export function leave({ employee: who, from, to, kind }) {
  parseDay(need(from, "from"));
  parseDay(need(to, "to"));
  return Object.freeze({ employee: need(who, "employee"), from, to, kind: oneOf(kind, LeaveKind, "leave kind") });
}
