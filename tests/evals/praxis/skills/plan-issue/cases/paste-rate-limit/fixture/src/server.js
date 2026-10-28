const http = require("node:http");
const { addPaste, getPaste } = require("./store");

const MAX_BYTES = 64 * 1024;

function send(res, status, body) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

function handle(req, res) {
  if (req.method === "POST" && req.url === "/pastes") {
    let text = "";
    req.on("data", (chunk) => (text += chunk));
    req.on("end", () => {
      if (!text || text.length > MAX_BYTES) return send(res, 400, { error: "empty or too large" });
      send(res, 201, { id: addPaste(text) });
    });
    return;
  }
  const match = req.method === "GET" && req.url.match(/^\/pastes\/(\d+)$/);
  const paste = match && getPaste(match[1]);
  if (paste) return send(res, 200, paste);
  send(res, 404, { error: "not found" });
}

const server = http.createServer(handle);
if (require.main === module) server.listen(process.env.PORT || 8080);
module.exports = { server };
