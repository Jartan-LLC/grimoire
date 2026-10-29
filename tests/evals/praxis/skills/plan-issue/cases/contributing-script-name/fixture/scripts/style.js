// The house style check: no tabs and no trailing spaces in src/ and test/.
const fs = require("node:fs");
const path = require("node:path");

let problems = 0;
for (const dir of ["src", "test"]) {
  for (const file of fs.readdirSync(dir)) {
    fs.readFileSync(path.join(dir, file), "utf8")
      .split("\n")
      .forEach((line, i) => {
        if (/\t| +$/.test(line)) {
          console.log(`${dir}/${file}:${i + 1}: tab or trailing space`);
          problems++;
        }
      });
  }
}
process.exitCode = problems ? 1 : 0;
