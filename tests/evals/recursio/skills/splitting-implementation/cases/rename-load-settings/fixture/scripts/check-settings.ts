import { loadSettings } from "../src/settings.ts";

const path = process.argv[2] ?? "standup.json";
try {
  const settings = loadSettings(path);
  console.log(`${path}: ${settings.members.length} members, deadline ${settings.deadline}`);
} catch (error) {
  console.error((error as Error).message);
  process.exit(1);
}
