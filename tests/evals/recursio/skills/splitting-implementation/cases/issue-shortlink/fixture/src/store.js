const crypto = require("node:crypto");

class MemoryStore {
  constructor() {
    this.links = new Map();
  }

  create(url) {
    const code = crypto.randomBytes(4).toString("hex");
    this.links.set(code, { url, createdAt: Date.now() });
    return code;
  }

  resolve(code) {
    const link = this.links.get(code);
    return link ? link.url : null;
  }

  remove(code) {
    return this.links.delete(code);
  }
}

module.exports = { MemoryStore };
