const members = require("./members");

function updateProfile(member, input) {
  const email = String(input.email || "").trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return { status: 400, error: "Enter an email address like name@example.com." };
  }
  const other = members.findByEmail(email);
  if (other && other.id !== member.id) {
    return { status: 409, error: "Another member already uses that email." };
  }
  return { status: 200, member: members.save({ ...member, email, name: input.name || member.name }) };
}

module.exports = { updateProfile };
