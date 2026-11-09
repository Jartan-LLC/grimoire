const assert = require('node:assert/strict');
const { test } = require('node:test');
const { ParseError } = require('../src/errors');

test('names the text it could not parse', () => {
  assert.match(new ParseError('3 parsecs', 'unknown unit').message, /3 parsecs/);
});
