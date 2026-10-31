// Prints each repository of the organisation with its star count, for the dashboard import.
import { repoStars } from "../src/github.js";
import { fetchJson } from "../src/http.js";

const org = process.argv[2] ?? "acme";
const repos = await fetchJson(`https://api.github.com/orgs/${org}/repos?per_page=100`);
for (const repo of repos) {
  console.log(`${repo.name}\t${await repoStars(org, repo.name)}`);
}
