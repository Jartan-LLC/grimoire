import { loadSettings, type Settings } from "./settings.ts";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/** Whether standup runs on the given date in the team's timezone. */
export function isStandupDay(settings: Settings, date: Date): boolean {
  const day = new Intl.DateTimeFormat("en-US", { weekday: "short", timeZone: settings.timezone })
    .format(date);
  return DAYS.includes(day) && !settings.quietDays.includes(day);
}

/** Whether the deadline has passed at `now`, in the team's timezone. */
export function pastDeadline(settings: Settings, now: Date): boolean {
  const time = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone: settings.timezone,
  }).format(now);
  return time >= settings.deadline;
}

export function standupToday(settingsPath: string, now: Date = new Date()): boolean {
  return isStandupDay(loadSettings(settingsPath), now);
}
