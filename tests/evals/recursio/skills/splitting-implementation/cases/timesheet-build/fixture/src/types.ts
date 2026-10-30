// The records the timesheet modules pass to one another.

export const REGIONS = ["US", "GB-ENG", "DE-BY", "FR"] as const;

export type Region = (typeof REGIONS)[number];

// One stretch of work. `start` and `end` are local wall-clock times without an offset,
// "2026-10-12T09:00", in the IANA zone `zone`. `minutes` is the real time elapsed between
// them, so a night that crosses a clock change is an hour longer or shorter than the
// wall clock says.
export interface Entry {
  person: string;
  project: string;
  start: string;
  end: string;
  zone: string;
  minutes: number;
  billable: boolean;
  note: string;
}

// A public holiday. `date` is the day it is observed, `actual` the day it falls on;
// both are "YYYY-MM-DD" and differ only when the holiday moved off a weekend.
export interface Holiday {
  date: string;
  actual: string;
  name: string;
  region: Region;
}

// An hourly rate in minor units of `currency` (cents, pence; yen have none). A null person
// or project matches any. The rate applies from `from` (inclusive) until `to` (exclusive),
// or with no end when `to` is null; both are "YYYY-MM-DD".
export interface Rate {
  person: string | null;
  project: string | null;
  from: string;
  to: string | null;
  hourly: number;
  currency: string;
}

// A line an importer could not read; `line` counts from 1.
export interface LineError {
  line: number;
  message: string;
}

export interface ImportResult {
  entries: Entry[];
  errors: LineError[];
}
