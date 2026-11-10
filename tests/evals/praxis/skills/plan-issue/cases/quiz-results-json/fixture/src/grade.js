// Mark answer sheets against the key.

// The scanner writes one row per student: name, then one letter per question.
function parseAnswers(csv) {
  return csv
    .trim()
    .split("\n")
    .slice(1)
    .map((line) => {
      const [student, ...letters] = line.split(",").map((cell) => cell.trim());
      return { student, letters };
    });
}

// The key is one letter per line, question 1 first.
function parseKey(text) {
  return text.trim().split("\n").map((line) => line.trim().toUpperCase());
}

function gradeAll(answers, key) {
  return answers.map(({ student, letters }) => ({
    student,
    score: letters.filter((letter, i) => letter.toUpperCase() === key[i]).length,
    outOf: key.length,
  }));
}

module.exports = { parseAnswers, parseKey, gradeAll };
