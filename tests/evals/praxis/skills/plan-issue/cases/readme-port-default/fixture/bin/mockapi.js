#!/usr/bin/env node
const http = require("node:http");
const { port } = require("../src/config");
const { respond } = require("../src/routes");

const dir = process.argv[2] || "mocks";
const listening = port(process.env);
http
  .createServer((req, res) => {
    const { status, body } = respond(dir, new URL(req.url, "http://x").pathname);
    res.writeHead(status, { "content-type": "application/json" });
    res.end(JSON.stringify(body));
  })
  .listen(listening, () => console.log(`mockapi: listening on ${listening}, serving ${dir}`));
