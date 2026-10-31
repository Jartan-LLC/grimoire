// Exits 1 when any service listed in services.json is down.
import { readFileSync } from "node:fs";
import { fetchJson } from "../src/http.js";
import { isUp } from "../src/status.js";

const services = JSON.parse(readFileSync(process.argv[2] ?? "services.json", "utf8"));
let down = 0;
for (const { name, url } of services) {
  const up = await isUp(url);
  if (!up) {
    down += 1;
    const detail = await fetchJson(`${url}/health/detail`).catch((error) => error.message);
    console.error(`${name} is down: ${JSON.stringify(detail)}`);
  }
}
process.exitCode = down ? 1 : 0;
