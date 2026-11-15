// The VEVENT blocks of one calendar file, each as its text and UID.
function events(text) {
  const blocks = text.match(/BEGIN:VEVENT[\s\S]*?END:VEVENT\r?\n?/g) ?? [];
  return blocks.map((block) => ({ block, uid: /^UID:(.*)$/m.exec(block)?.[1].trim() }));
}

module.exports = { events };
