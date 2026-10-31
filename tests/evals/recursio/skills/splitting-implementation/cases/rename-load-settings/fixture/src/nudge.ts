import { loadSettings, type Settings } from "./settings.ts";
import type { Note } from "./digest.ts";

/** The members who have written no note yet. */
export function missing(settings: Settings, notes: Note[]): string[] {
  const written = new Set(notes.map((note) => note.author));
  return settings.members.filter((member) => !written.has(member));
}

export function nudgeMessages(settingsPath: string, notes: Note[]): string[] {
  const settings = loadSettings(settingsPath);
  return missing(settings, notes).map(
    (member) => `@${member} standup notes are due by ${settings.deadline} (${settings.timezone}).`,
  );
}
