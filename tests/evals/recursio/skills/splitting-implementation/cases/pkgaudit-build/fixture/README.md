# pkgaudit

Audits a Node project's lockfile: which licenses it ships, which packages are installed at more
than one version, and whether it keeps to the project's policy. A library and a command, written
in TypeScript that Node 24 runs directly (erasable syntax only: no `enum`, no `namespace`, no
parameter properties; imports name the `.ts` file). No npm dependencies.

## Contract

`src/types.ts` holds what the modules pass to one another: `Package`, `Finding`, `Policy`,
`Severity` with the ordered `SEVERITIES`, and `AuditError`. Each module below uses only these and
nothing of its siblings; only the command uses them all. Every module throws `AuditError` for
input it refuses.

## Lockfiles (`src/lockfiles.ts`)

Both readers return `Package[]` sorted by name, then version, then path.

- `readPackageLock(text)`: npm's `package-lock.json` or `npm-shrinkwrap.json`, `lockfileVersion` 2
  or 3, from its `packages` map. Version 1 throws `lockfile v1 is not supported; run npm install
  with npm 7 or later`; text that is not JSON throws with the parser's position.
  - The `""` key is the project itself and is skipped. Keys are install paths:
    `node_modules/a`, `node_modules/a/node_modules/b`, `node_modules/@scope/c`. The name is what
    follows the last `node_modules/` (two segments when scoped), unless the entry has a `name`
    field, which wins (aliases). `path` is the key.
  - Entries with `link: true` and keys without `node_modules/` (workspace sources) are skipped.
  - `dev` is true when `dev` or `devOptional` is true.
  - `license` is the `license` string; the legacy object `{ "type": "MIT" }` gives its type; the
    legacy array `licenses: [{ "type": "MIT" }, { "type": "Apache-2.0" }]` gives `(MIT OR
    Apache-2.0)`; none is null. `resolved` and `integrity` are copied, null when absent.
- `readYarnLock(text)`: yarn classic's `yarn.lock`, format v1.
  - Lines starting with `#` are comments. An entry starts at column 0 with one or more
    comma-separated specifiers and a colon: `lodash@^4.17.0, lodash@^4.17.21:` or
    `"@babel/core@^7.0.0", "@babel/core@^7.1.0":`. Keys may be quoted, with backslash escapes. The
    name is the specifier up to its last `@` that is not the first character.
  - Fields are indented two spaces, `key value` with the value quoted or bare: `version "7.1.2"`,
    `resolved "https://..."`, `integrity sha512-...`. Nested blocks (`dependencies:`,
    `optionalDependencies:`, indented four spaces) are skipped.
  - `dev` is false and `license` null (yarn records neither); `path` is the first specifier.
  - A lockfile with a `__metadata:` entry (yarn berry) throws `yarn berry lockfiles are not
    supported`. An entry without `version`, a line indented wrongly, or the same specifier twice
    throws with its line number.
- `readLockfile(path)`: picks the reader by file name and puts the path in any `AuditError`.

## Versions and ranges (`src/semver.ts`)

- `parse(text)`: SemVer 2.0.0 to `{ major, minor, patch, prerelease, build }`, or null when
  invalid. A leading `v` or `=` and surrounding spaces are dropped. Numeric parts and numeric
  prerelease identifiers have no leading zeros; identifiers are `[0-9A-Za-z-]+` and never empty.
  Numeric prerelease identifiers become numbers.
- `compare(a, b)`: -1, 0 or 1 by precedence. Major, minor and patch compare as numbers; a
  prerelease sorts before its release; prerelease identifiers compare left to right, numbers as
  numbers and below any alphanumeric, alphanumerics in ASCII order, and a shorter list sorts first
  when the longer starts with it. Build metadata is ignored. The spec's chain holds: `1.0.0-alpha`
  < `1.0.0-alpha.1` < `1.0.0-alpha.beta` < `1.0.0-beta` < `1.0.0-beta.2` < `1.0.0-beta.11` <
  `1.0.0-rc.1` < `1.0.0`.
- `parseRange(text)`: npm's range grammar to a list of comparator sets, OR between the sets
  (`||`), AND within one (space-separated). An invalid range throws.
  - Primitives: `<`, `<=`, `>`, `>=`, `=` and a bare version. `>1.2` means `>=1.3.0`; `<=1.2`
    means `<1.3.0-0`.
  - X-ranges: `*` and the empty string match any version; `1.x` and `1` mean `>=1.0.0 <2.0.0-0`;
    `1.2.x` and `1.2` mean `>=1.2.0 <1.3.0-0`. `X` and `*` work like `x`.
  - Tilde: `~1.2.3` is `>=1.2.3 <1.3.0-0`, `~1.2` is `>=1.2.0 <1.3.0-0`, `~1` is
    `>=1.0.0 <2.0.0-0`, `~0.2.3` is `>=0.2.3 <0.3.0-0`.
  - Caret, which keeps the leftmost non-zero part: `^1.2.3` is `>=1.2.3 <2.0.0-0`, `^0.2.3` is
    `>=0.2.3 <0.3.0-0`, `^0.0.3` is `>=0.0.3 <0.0.4-0`, `^1.2.x` is `>=1.2.0 <2.0.0-0`, `^0.0.x`
    and `^0.0` are `>=0.0.0 <0.1.0-0`, `^1.x` is `>=1.0.0 <2.0.0-0`.
  - Hyphen ranges: `1.2.3 - 2.3.4` is `>=1.2.3 <=2.3.4`; a partial first version fills with
    zeros (`1.2 - 2.3.4` is `>=1.2.0 <=2.3.4`); a partial second version is an X-range bound
    (`1.2.3 - 2.3` is `>=1.2.3 <2.4.0-0`, `1.2.3 - 2` is `>=1.2.3 <3.0.0-0`).
- `satisfies(version, range)`: true when the version meets every comparator of some set. A version
  with a prerelease also needs a comparator in that set with the same major, minor and patch and a
  prerelease of its own: `1.2.3-alpha.7` satisfies `>1.2.3-alpha.3` but `3.4.5-alpha.9` does not,
  and `^1.2.3` matches no `1.5.0-beta`. An invalid version is false.
- `sortVersions(versions)` ascending by precedence, `maxSatisfying(versions, range)` (null when none).

## SPDX expressions (`src/spdx.ts`)

- `parseExpression(text)`: an SPDX 2.3 license expression to a tree of `{ type: "license", id,
  plus, exception, known }` and `{ type: "and" | "or", left, right }` nodes.
  - Precedence, tightest first: `WITH`, `AND`, `OR`; AND and OR group left to right; parentheses
    override. Operators are upper case: `mit and isc` throws `unknown operator "and"; use AND`.
  - Ids are `[A-Za-z0-9.-]+`, matched case-insensitively against the module's table of known
    licenses and written in its case: MIT, ISC, 0BSD, BSD-2-Clause, BSD-3-Clause, Apache-2.0,
    MPL-2.0, Zlib, BSL-1.0, Unlicense, CC0-1.0, CC-BY-4.0, BlueOak-1.0.0, Python-2.0, Artistic-2.0,
    LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, LGPL-3.0-or-later, GPL-2.0-only,
    GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later, AGPL-3.0-only, AGPL-3.0-or-later. An unknown
    id parses, with `known: false`.
  - Deprecated ids are rewritten: `GPL-2.0` to `GPL-2.0-only`, `GPL-2.0+` to `GPL-2.0-or-later`,
    and likewise for GPL-3.0, LGPL-2.1, LGPL-3.0 and AGPL-3.0.
  - A trailing `+` sets `plus`. `LicenseRef-x` and `DocumentRef-y:LicenseRef-x` are ids too.
  - The right of `WITH` must be a known exception (`Classpath-exception-2.0`, `LLVM-exception`,
    `GCC-exception-3.1`) or throw; `WITH` applies to a single license, never to a group.
  - Before parsing, package.json habits are mapped: `UNLICENSED` to `LicenseRef-proprietary`, `SEE
    LICENSE IN <file>` to `LicenseRef-see-license-file`, `Apache 2.0` and `Apache2` to
    `Apache-2.0`. An empty expression, an unbalanced parenthesis, or a dangling operator throws
    with the character position.
- `formatExpression(node)`: the canonical text, with parentheses only around an OR inside an AND:
  `mit OR (apache-2.0 AND bsd-3-clause)` formats as `MIT OR Apache-2.0 AND BSD-3-Clause`.
- `evaluate(node, policy)`: `{ verdict, reason, choice }`, the verdict `allowed`, `denied` or
  `unknown` (neither list names it).
  - A license is denied when `deny` names it, else allowed when `allow` names it. `X+` is decided
    by `X` or `X-or-later` (`GPL-2.0+` matches either); `LicenseRef-*` in a list matches every
    LicenseRef. A license `WITH` an exception is decided by an entry for the whole
    `id WITH exception` when the policy has one, otherwise by the bare license.
  - OR is allowed when either side is, denied when both are, otherwise unknown; `choice` is the
    first allowed alternative, in text order. AND is denied when either side is, allowed when both
    are, otherwise unknown.
  - `reason` names the license that decided, as `GPL-3.0-only is denied`.

## Reports (`src/report.ts`)

- `sortFindings(findings)`: by severity in `SEVERITIES` order, then package name, then version with
  a numeric collation (`1.10.0` after `1.9.0`), then rule.
- `summary(findings)`: `5 findings: 1 critical, 2 high, 0 moderate, 2 low, 0 info`, or
  `No findings.` (`1 finding:` in the singular).
- `renderText(findings, { color = false })`: one line per finding, columns severity (upper case,
  padded to 8), `package@version` (padded to the longest), rule (padded likewise) and message, two
  spaces apart; then a blank line and the summary. With `color`, critical and high are red
  (`ESC[31m`), moderate yellow (`ESC[33m`), low and info dim (`ESC[2m`), each reset after the
  severity word only.
- `renderJson(findings, { generatedAt })`: two-space indented JSON ending in a newline, keys in
  this order: `version` (1), `generatedAt`, `summary` (a count for every severity), `findings`
  (sorted).
- `renderMarkdown(findings)`: a `# pkgaudit report` heading, the summary as a paragraph, then a
  `## Critical` (and so on) section per severity that has findings, each a table with columns
  Package, Version, Rule and Message. A `|` in a message is escaped as `\|` and a newline becomes
  `<br>`.
- `exitCode(findings, failOn)`: 1 when any finding is at `failOn` or more severe, else 0.

## Command (`src/cli.ts`)

Run as `node src/cli.ts` or through the package's `pkgaudit` bin. Every subcommand takes
`--format text|json|markdown` (default text, colored when stdout is a terminal) and `--prod`, which
leaves out dev packages, and reads `LOCKFILE`.

- `pkgaudit licenses [--policy FILE] [--node-modules DIR] LOCKFILE`: checks every package's license
  against the policy (default: allow MIT, ISC, BSD-2-Clause, BSD-3-Clause, Apache-2.0 and 0BSD,
  deny nothing). `--node-modules` fills a missing license from `DIR/<path>/package.json`, which
  yarn needs. Rules: `license-denied` (high), `license-unknown` (moderate; no license, or the
  verdict is unknown), `license-invalid` (moderate; the expression does not parse, message the
  parse error).
- `pkgaudit duplicates LOCKFILE`: one `duplicate` finding per name installed at two or more
  versions, the message listing them in version order with their copy counts, as `2 versions:
  4.17.20 (x3), 4.17.21`. Severity low when they all share a major version (they could dedupe),
  info when they do not.
- `pkgaudit check --policy FILE [--fail-on SEVERITY] LOCKFILE`: the license and duplicate checks
  plus `pin-violated` (high) for each installed version outside its package's pin. Then the
  policy's `severity` overrides apply, its `ignore` entries drop findings (a name, or `name@range`
  matched with `satisfies`), and the report prints. Exit 1 when `exitCode` says so for `--fail-on`
  (default high).

The policy file is JSON with the `Policy` fields, each optional. An `AuditError` prints
`pkgaudit: FILE: message` to stderr (no `FILE:` when it has none) and exits 2, as does a usage
error, after a usage line. `licenses` and `duplicates` exit 0 whatever they find.

## Status

Only the contract exists. Each module gets its own test file in `test/`.
