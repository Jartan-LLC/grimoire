import { readFileSync } from "node:fs";

export interface Settings {
  channel: string;
  timezone: string;
  deadline: string;
  members: string[];
  quietDays: string[];
}

const DEFAULTS: Settings = {
  channel: "#standup",
  timezone: "UTC",
  deadline: "10:00",
  members: [],
  quietDays: ["Sat", "Sun"],
};

/** Reads the team's settings file; fields it leaves out take the defaults. */
export function loadSettings(
  path: string,
  read: (path: string) => string = (p) => readFileSync(p, "utf8"),
): Settings {
  const raw = JSON.parse(read(path)) as Partial<Settings>;
  const settings = { ...DEFAULTS, ...raw };
  if (!/^\d{2}:\d{2}$/.test(settings.deadline)) {
    throw new Error(`${path}: deadline must be HH:MM, got ${settings.deadline}`);
  }
  return settings;
}
