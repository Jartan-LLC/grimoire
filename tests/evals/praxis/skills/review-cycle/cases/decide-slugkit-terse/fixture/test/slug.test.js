'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { slugify } = require('../src/slug');

test('joins words with a dash', () => {
  assert.strictEqual(slugify('Hello, World!'), 'hello-world');
});

test('cuts the slug to maxLength', () => {
  assert.strictEqual(slugify('Hello World', { maxLength: 5 }), 'hello');
});
