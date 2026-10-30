const { Sink } = require("./sink");

class MemorySink extends Sink {
  constructor() {
    super();
    this.pending = [];
    this.flushed = [];
  }

  record(metric) {
    this.pending.push(metric);
  }

  async flush() {
    this.flushed.push(...this.pending);
    this.pending = [];
  }
}

module.exports = { MemorySink };
