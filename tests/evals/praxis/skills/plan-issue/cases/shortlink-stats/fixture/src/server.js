const http = require("node:http");
const { handle } = require("./app");

http
  .createServer(async (req, res) => {
    let raw = "";
    for await (const chunk of req) raw += chunk;
    const { status, headers = {}, body } = handle(req.method, req.url, raw ? JSON.parse(raw) : {});
    res.writeHead(status, { "content-type": "application/json", ...headers });
    res.end(body ? JSON.stringify(body) : "");
  })
  .listen(process.env.PORT || 3000);
