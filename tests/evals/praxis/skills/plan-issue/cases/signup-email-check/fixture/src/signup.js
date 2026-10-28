const crypto = require("node:crypto");
const members = require("./members");

function signup(input) {
  const email = String(input.email || "").trim().toLowerCase();
  if (!input.name) {
    return { status: 400, error: "Enter your name." };
  }
  if (members.findByEmail(email)) {
    return { status: 409, error: "Another member already uses that email." };
  }
  const member = { id: crypto.randomUUID(), name: input.name, email, joined: new Date().toISOString() };
  return { status: 201, member: members.save(member) };
}

module.exports = { signup };
