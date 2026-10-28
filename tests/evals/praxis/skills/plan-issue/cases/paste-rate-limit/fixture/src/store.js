// Pastes in memory, by id.
const pastes = new Map();
let nextId = 1;

function addPaste(text) {
  const id = String(nextId++);
  pastes.set(id, { id, text, created: new Date().toISOString() });
  return id;
}

function getPaste(id) {
  return pastes.get(id);
}

module.exports = { addPaste, getPaste };
