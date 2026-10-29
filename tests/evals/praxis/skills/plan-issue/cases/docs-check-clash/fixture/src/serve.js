const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

function run() {
  http
    .createServer((req, res) => {
      const file = path.join("site", req.url === "/" ? "index.html" : req.url);
      fs.readFile(file, (err, body) => {
        res.writeHead(err ? 404 : 200);
        res.end(err ? "not found" : body);
      });
    })
    .listen(4000);
}

module.exports = { run };
