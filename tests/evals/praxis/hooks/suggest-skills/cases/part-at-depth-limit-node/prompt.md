Start one general-purpose subagent with exactly this brief, then pass on its report.

# Brief: unitparse parsers

Depth: two levels below the main thread.
You are at the depth limit: build your part and never split.

Scope: write only src/parsers/length.js, src/parsers/mass.js, src/parsers/duration.js and
test/length.test.js, test/mass.test.js, test/duration.test.js; everything else is read-only.
Contract, read-only: src/errors.js.
Test command, your tests only: node --test test/
Requirements: README.md, every bullet.
Settled decisions you touch: CommonJS modules, as src/errors.js is.
Skills to load: none named.
Do not stage, commit, push or switch branches. Ask no questions; report instead.

Report: outcome; the test command and its terse output; files written.
