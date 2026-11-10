#!/usr/bin/env node
// quizmark grade <answers.csv> <key.txt>: print each student's score.

const fs = require("node:fs");
const { parseAnswers, parseKey, gradeAll } = require("../src/grade");
const { formatTable } = require("../src/table");

function main(argv) {
  const [command, answersPath, keyPath] = argv;
  if (command !== "grade" || !answersPath || !keyPath) {
    console.error("usage: quizmark grade <answers.csv> <key.txt>");
    return 2;
  }
  const answers = parseAnswers(fs.readFileSync(answersPath, "utf8"));
  const key = parseKey(fs.readFileSync(keyPath, "utf8"));
  console.log(formatTable(gradeAll(answers, key)));
  return 0;
}

process.exitCode = main(process.argv.slice(2));
