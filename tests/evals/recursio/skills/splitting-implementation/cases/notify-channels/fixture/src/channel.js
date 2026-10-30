// Every channel implements send(message) and resolves to { ok, id }, or rejects with a ChannelError.
class ChannelError extends Error {
  constructor(channel, reason) {
    super(`${channel}: ${reason}`);
    this.channel = channel;
    this.reason = reason;
  }
}

module.exports = { ChannelError };
