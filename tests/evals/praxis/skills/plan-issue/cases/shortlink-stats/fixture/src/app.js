const crypto = require("node:crypto");
const store = require("./store");

// One request in, one response out: { status, headers, body }.
function handle(method, path, body) {
  if (method === "POST" && path === "/links") {
    if (!/^https?:\/\//.test(body.url || "")) return { status: 400, body: { error: "url must be http(s)" } };
    const code = crypto.randomBytes(4).toString("base64url");
    store.put(code, { url: body.url, created: new Date().toISOString() });
    return { status: 201, body: { code } };
  }
  const link = method === "GET" ? store.get(path.slice(1)) : undefined;
  if (!link) return { status: 404, body: { error: "not found" } };
  return { status: 302, headers: { location: link.url } };
}

module.exports = { handle };
