const { ChannelError } = require("./channel");

class ConsoleChannel {
  constructor(write = (line) => process.stdout.write(line + "\n")) {
    this.write = write;
    this.sent = 0;
  }

  async send(message) {
    if (!message.text) throw new ChannelError("console", "empty message");
    this.sent += 1;
    this.write(`[${message.priority || "normal"}] ${message.text}`);
    return { ok: true, id: `console-${this.sent}` };
  }
}

module.exports = { ConsoleChannel };
