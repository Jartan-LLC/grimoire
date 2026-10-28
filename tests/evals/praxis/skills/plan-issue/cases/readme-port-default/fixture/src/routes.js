const fs = require("node:fs");
const path = require("node:path");

// The canned response for `urlPath`: mocks/users.json answers /users.
function respond(dir, urlPath) {
  const file = path.join(dir, `${urlPath.replace(/^\/+|\/+$/g, "") || "index"}.json`);
  if (!fs.existsSync(file)) return { status: 404, body: { error: "no mock for " + urlPath } };
  const { _status = 200, ...body } = JSON.parse(fs.readFileSync(file, "utf8"));
  return { status: _status, body };
}

module.exports = { respond };
