function countdown(minutes) {
  const marks = [];
  for (let left = minutes; left > 0; left -= 5) marks.push(left);
  return marks;
}

function runSession(minutes, { bell }, tick = setTimeout) {
  for (const left of countdown(minutes)) {
    tick(() => console.log(`${left} min left`), (minutes - left) * 60000);
  }
  tick(() => console.log(bell ? "\u0007Time's up" : "Time's up"), minutes * 60000);
}

module.exports = { countdown, runSession };
