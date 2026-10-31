import { digestFromFile } from "../src/digest.ts";
import { standupToday } from "../src/schedule.ts";
import { loadSettings } from "../src/settings.ts";

const path = process.argv[2] ?? "standup.json";
const settings = loadSettings(path);
if (standupToday(path)) {
  // The channel client reads the digest from stdout.
  console.log(settings.channel);
  console.log(digestFromFile(path, []));
}
