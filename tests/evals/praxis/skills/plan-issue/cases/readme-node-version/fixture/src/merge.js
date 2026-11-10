const { events } = require("./events");

// One calendar holding every event of `texts`, the first copy of each UID kept.
function merge(texts) {
  const seen = new Set();
  const kept = [];
  for (const { block, uid } of texts.flatMap(events)) {
    if (uid && seen.has(uid)) continue;
    seen.add(uid);
    kept.push(block.endsWith("\n") ? block : block + "\r\n");
  }
  return ["BEGIN:VCALENDAR\r\nVERSION:2.0\r\n", ...kept, "END:VCALENDAR\r\n"].join("");
}

module.exports = { merge };
