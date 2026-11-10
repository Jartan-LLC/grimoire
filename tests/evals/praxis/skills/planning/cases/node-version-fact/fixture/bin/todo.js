#!/usr/bin/env node
const { load } = require('../src/store');

const [cmd] = process.argv.slice(2);
if (cmd === 'list') {
  for (const t of load()) console.log(`${t.done ? 'x' : ' '} ${t.id} ${t.text}`);
} else {
  console.error('usage: todo list');
  process.exit(2);
}
