const http = require("node:http");
const { signup } = require("./signup");
const { updateProfile } = require("./profile");

http
  .createServer(async (req, res) => {
    let body = "";
    for await (const chunk of req) body += chunk;
    const input = body ? JSON.parse(body) : {};
    const result =
      req.url === "/signup" ? signup(input) : req.url === "/profile" ? updateProfile(input.member, input) : { status: 404 };
    res.writeHead(result.status, { "content-type": "application/json" });
    res.end(JSON.stringify(result));
  })
  .listen(process.env.PORT || 3000);
