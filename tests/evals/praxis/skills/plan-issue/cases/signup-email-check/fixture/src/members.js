// The member list, kept in memory and written to members.json by the server on shutdown.
const members = new Map();

function findByEmail(email) {
  return [...members.values()].find((m) => m.email === email);
}

function save(member) {
  members.set(member.id, member);
  return member;
}

function reset() {
  members.clear();
}

module.exports = { findByEmail, save, reset, members };
