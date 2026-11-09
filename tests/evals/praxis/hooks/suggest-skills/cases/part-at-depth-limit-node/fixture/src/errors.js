class ParseError extends Error {
  constructor(text, reason) {
    super(`cannot parse ${JSON.stringify(text)}: ${reason}`);
    this.name = 'ParseError';
  }
}

module.exports = { ParseError };
