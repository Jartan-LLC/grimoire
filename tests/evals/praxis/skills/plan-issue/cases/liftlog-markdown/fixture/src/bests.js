// The heaviest set of each lift per lifter; on equal weight, the one with more reps.
function personalBests(sessions) {
  const best = new Map();
  for (const session of sessions) {
    for (const set of session.sets) {
      const key = `${session.lifter}/${set.lift}`;
      const held = best.get(key);
      if (!held || set.kg > held.kg || (set.kg === held.kg && set.reps > held.reps)) {
        best.set(key, { lifter: session.lifter, lift: set.lift, kg: set.kg, reps: set.reps, date: session.date });
      }
    }
  }
  return [...best.values()].sort((a, b) => a.lifter.localeCompare(b.lifter) || a.lift.localeCompare(b.lift));
}

module.exports = { personalBests };
