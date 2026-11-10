// Bookmarks on disk: one JSON array in the marks file.
// Written before fs/promises: every function takes a Node-style callback, and add nests
// load inside it. Moving to promises would change every caller.
const fs = require("node:fs");

function load(file, cb) {
  fs.readFile(file, "utf8", (err, text) => {
    if (err && err.code === "ENOENT") return cb(null, []);
    if (err) return cb(err);
    cb(null, JSON.parse(text));
  });
}

function save(file, marks, cb) {
  fs.writeFile(file, JSON.stringify(marks, null, 2) + "\n", cb);
}

function add(file, mark, cb) {
  load(file, (err, marks) => {
    if (err) return cb(err);
    marks.push(mark);
    save(file, marks, cb);
  });
}

module.exports = { load, save, add };
