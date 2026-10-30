// A metric: { name, type: "counter" | "gauge" | "timer", value, tags: { key: value } }.
// A sink keeps what record() gives it and writes it out on flush().
class Sink {
  record(metric) {
    throw new Error("record() not implemented");
  }

  async flush() {
    throw new Error("flush() not implemented");
  }
}

module.exports = { Sink };
