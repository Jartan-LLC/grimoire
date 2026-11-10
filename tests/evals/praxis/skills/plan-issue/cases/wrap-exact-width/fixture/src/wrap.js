// Wrap `text` into lines of at most `width` characters, breaking at spaces.
// A word longer than `width` goes on a line of its own, unbroken.
function wrap(text, width) {
  const lines = [];
  let line = "";
  for (const word of text.split(/\s+/).filter(Boolean)) {
    if (line && line.length + 1 + word.length >= width) {
      lines.push(line);
      line = word;
    } else {
      line = line ? line + " " + word : word;
    }
  }
  if (line) lines.push(line);
  return lines;
}

module.exports = { wrap };
