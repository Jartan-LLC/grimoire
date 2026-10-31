import { loadSettings, type Settings } from "./settings.ts";

export interface Note {
  author: string;
  text: string;
}

/** The digest text: one line per member, in the settings' order, notes or a dash. */
export function buildDigest(settings: Settings, notes: Note[]): string {
  const lines = settings.members.map((member) => {
    const mine = notes.filter((note) => note.author === member).map((note) => note.text);
    return `*${member}*: ${mine.length > 0 ? mine.join(" / ") : "-"}`;
  });
  return [`Standup digest for ${settings.channel}`, ...lines].join("\n");
}

export function digestFromFile(settingsPath: string, notes: Note[]): string {
  return buildDigest(loadSettings(settingsPath), notes);
}
