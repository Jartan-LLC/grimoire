import { fetchJson } from "./http.js";

const API = "https://api.github.com";

/**
 * @param {string} owner
 * @param {string} repo
 * @returns {Promise<number>}
 */
export async function repoStars(owner, repo) {
  const data = await fetchJson(`${API}/repos/${owner}/${repo}`);
  return data.stargazers_count;
}

/**
 * The names of an organisation's public repositories.
 * @param {string} org
 * @returns {Promise<string[]>}
 */
export async function orgRepos(org) {
  const repos = await fetchJson(`${API}/orgs/${org}/repos?per_page=100`);
  return repos.map((repo) => repo.name);
}
