#!/usr/bin/env node
/**
 * Duplicate-comment finder -- a reviewer tool, NOT a hook. It sits under
 * hooks/scripts/ only to reuse lib/; nothing in hooks.json invokes it.
 *
 * It runs against whatever repo is being reviewed, which is not this one. Keep
 * it free of assumptions about this repo's layout: a rule that suppresses a
 * finding here silently suppresses real ones in every repo praxis reviews.
 *
 * The Retold fact rule cannot be applied from one file: judging a comment as a
 * retelling means knowing whether the same fact is told elsewhere, which
 * per-file review structurally cannot see. This supplies that whole-repo view,
 * scoped to the diff -- comment lines ADDED by the change whose prose already
 * appears somewhere tracked, naming both sites so the reviewer picks a keeper.
 *
 * Usage:
 *   node find-duplicate-comments.js [base-ref] [--skip <segment>]...
 *
 *   base-ref  defaults to origin/main
 *   --skip    extra path segments to ignore, repeatable and matched literally.
 *             node_modules is always skipped; add generated trees here, e.g.
 *             --skip dist --skip build
 */

const { spawnSync } = require('child_process');

const MIN_PROSE_CHARS = 25;

// Comment openers across the languages this marketplace touches. Deliberately
// loose: a false positive costs a reviewer one glance, a miss costs the rule.
const COMMENT_PATTERNS = [
  /^\s*\/\/+\s?(.*)$/,
  /^\s*#+\s?(.*)$/,
  /^\s*\*\s?(.*)$/,
  /^\s*\/\*+\s?(.*?)(?:\*\/)?\s*$/
];

// Mandated or machine-read text is meant to be identical everywhere, so it is
// never a retelling.
const EXEMPT = /SPDX-License-Identifier|Copyright|Licensed under|eslint-|prettier-|type:\s*ignore|noqa|@ts-|shellcheck\s+disable/i;

// Only what is universal. Generated trees are worth skipping too -- duplication
// there is the generator's, not an author's -- but their paths differ per repo,
// so they come from --skip rather than being guessed here.
const ALWAYS_SKIP = ['node_modules'];

/**
 * Path-segment matcher for the skip list. Segments are matched literally and
 * whole, so `dist` skips `dist/` and `a/dist/b` but never `redistribute.js`.
 *
 * Escaping is not cosmetic. Taken as patterns, a caller's `--skip .*` would
 * compile happily, match every path, and report a clean tree -- the silent
 * false-clean this tool exists to avoid producing.
 */
function escapeRegExp(segment) {
  return segment.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function buildSkipMatcher(extra) {
  const parts = [...ALWAYS_SKIP, ...extra].map(escapeRegExp);
  return new RegExp(`(^|/)(${parts.join('|')})(/|$)`);
}

function parseArgs(argv) {
  const skips = [];
  let base = null;

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--skip') {
      const value = argv[++i];
      if (!value) die('--skip needs a pattern');
      skips.push(value);
    } else if (arg.startsWith('--skip=')) {
      skips.push(arg.slice('--skip='.length));
    } else if (arg.startsWith('-')) {
      die(`unknown option '${arg}'`);
    } else if (base === null) {
      base = arg;
    } else {
      die(`unexpected argument '${arg}'`);
    }
  }

  return { base: base || 'origin/main', skips };
}


/**
 * Run git, returning stdout, or null when the command failed. The distinction is
 * load-bearing: a tool that reports "nothing found" because git errored is worse
 * than one that reports nothing at all, since a clean result is what a reviewer
 * acts on. Callers must treat null as fatal, not as empty.
 */
function git(args) {
  const r = spawnSync('git', args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  // A maxBuffer overflow sets .error while leaving truncated stdout in place,
  // which would silently drop a file from the index.
  if (r.error || r.status !== 0) return null;
  return r.stdout;
}

function die(message) {
  console.error(`find-duplicate-comments: ${message}`);
  process.exit(2);
}

/**
 * Read many blobs in one process. Returns their contents positionally, with
 * null where a spec did not resolve, or null overall if the batch itself failed.
 *
 * Input specs are NUL-delimited (`-z`) so a spec built from an awkward path
 * survives verbatim instead of being re-quoted. Output is unaffected by `-z`:
 * cat-file frames each blob as `<sha> <type> <size>\n<size bytes>\n`, and a
 * missing spec as `<spec> missing\n`. Sizes are in bytes, so the payload is
 * sliced from a Buffer -- decoding first would misplace every boundary after
 * the first multi-byte character.
 */
function gitBatch(specs) {
  const r = spawnSync('git', ['cat-file', '--batch', '-z'], {
    input: specs.join('\0') + '\0',
    // One response aggregates every tracked blob at once, unlike git()'s
    // per-command output, so this cap sits far above it. Batching trades
    // granularity for spawns: an overflow ends the run, where a per-file read
    // would have cost one file. Accepted: it fails loud.
    maxBuffer: 512 * 1024 * 1024
  });
  if (r.error || r.status !== 0) return null;

  const out = r.stdout;
  const results = [];
  let pos = 0;

  for (let i = 0; i < specs.length; i++) {
    const nl = out.indexOf('\n', pos);
    if (nl === -1) return null;
    const header = out.toString('utf8', pos, nl);
    pos = nl + 1;

    if (header.endsWith(' missing')) {
      results.push(null);
      continue;
    }

    const size = Number.parseInt(header.split(' ')[2], 10);
    if (!Number.isFinite(size)) return null;
    results.push(out.toString('utf8', pos, pos + size));
    pos += size + 1; // trailing newline git adds after each blob
  }
  return results;
}

/** Reduce a comment line to comparable prose, or '' when it carries none. */
function prose(line) {
  // A CRLF-committed blob leaves a trailing \r that the `(.*)$` patterns reject,
  // silently hiding // # * comments; drop it before matching.
  line = line.replace(/\r$/, '');
  for (const pattern of COMMENT_PATTERNS) {
    const m = line.match(pattern);
    if (m) {
      const text = (m[1] || '').trim();
      if (!text || EXEMPT.test(text)) return '';
      // Compare on words alone so punctuation and wrapping do not hide a twin.
      const normalized = text.toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
      return normalized.length >= MIN_PROSE_CHARS ? normalized : '';
    }
  }
  return '';
}

/**
 * Tracked paths at HEAD, minus submodule gitlinks and skipped trees, or null
 * when git failed.
 *
 * `-z` turns off the quoting `ls-files` otherwise applies to non-ASCII or
 * special-character paths; re-feeding a quoted display string as a spec would
 * silently miss the file -- the false-clean this tool exists to avoid. `-s`
 * carries the mode, the only way to spot a submodule gitlink (160000): it has
 * no blob to index and, fed to `cat-file --batch`, answers `<sha> submodule`,
 * which would abort the whole batch.
 */
function trackedPaths(skipMatcher) {
  const raw = git(['ls-files', '-s', '-z']);
  if (raw === null) return null;

  const paths = [];
  for (const record of raw.split('\0')) {
    if (!record) continue;
    // `<mode> <sha> <stage>\t<path>`; a path may itself hold spaces or tabs, so
    // take it whole after the first tab and read the mode before the first space.
    const path = record.slice(record.indexOf('\t') + 1);
    const mode = record.slice(0, record.indexOf(' '));
    if (mode === '160000' || skipMatcher.test(path)) continue;
    paths.push(path);
  }
  return paths;
}

/**
 * Map every comment's prose to the sites that carry it, across the whole tree at
 * HEAD -- a retelling counts whether or not the other site was touched here.
 * Null when git failed.
 *
 * One `git cat-file --batch` rather than a `git show` per file: this runs
 * against arbitrary repos, where per-file spawns scale with the checkout.
 */
function buildCommentIndex(files) {
  if (files.length === 0) return new Map();

  const batch = gitBatch(files.map(f => `HEAD:${f}`));
  if (batch === null) return null;

  const index = new Map();
  files.forEach((file, i) => {
    const content = batch[i];
    // Missing at HEAD (newly added) is normal -- nothing to index either way.
    if (!content) return;
    content.split('\n').forEach((line, n) => {
      const text = prose(line);
      if (!text) return;
      if (!index.has(text)) index.set(text, []);
      index.get(text).push(`${file}:${n + 1}`);
    });
  });
  return index;
}

/**
 * Walk one file's diff text, reporting added comment lines whose prose already
 * appears elsewhere in the index. Takes the diff rather than fetching it, so the
 * line-number bookkeeping below can be exercised without a checkout.
 */
function findRetoldInDiff(diffText, file, index) {
  const findings = [];
  let lineNo = 0;

  for (const line of diffText.split('\n')) {
    const hunk = line.match(/^@@ -\d+(?:,\d+)? \+(\d+)/);
    if (hunk) { lineNo = parseInt(hunk[1], 10); continue; }
    // "\ No newline at end of file" annotates the previous line rather than
    // being one, so counting it shifts every later line number by one.
    if (line.startsWith('\\')) continue;
    if (line.startsWith('-')) continue;
    if (!line.startsWith('+')) { lineNo++; continue; }

    const text = prose(line.slice(1));
    const here = `${file}:${lineNo}`;
    lineNo++;
    if (!text) continue;

    const elsewhere = (index.get(text) || []).filter(site => site !== here);
    if (elsewhere.length === 0) continue;

    findings.push({ here, text, elsewhere });
  }
  return findings;
}

/**
 * Drop the mirror image of a retelling whose sides were both added here: each
 * side finds the other, and without this the reviewer reads every pair twice.
 */
function dedupePairs(findings) {
  const reported = new Set();
  return findings.filter(f => {
    const pairKey = [f.here, ...f.elsewhere].sort().join('|');
    if (reported.has(pairKey)) return false;
    reported.add(pairKey);
    return true;
  });
}

function report(findings) {
  if (findings.length === 0) {
    console.log('No retold comments found in the diff.');
    return;
  }

  console.log(`${findings.length} added comment line(s) already told elsewhere:\n`);
  for (const f of findings) {
    console.log(`  ${f.here}`);
    console.log(`    "${f.text}"`);
    console.log(`    also at: ${f.elsewhere.slice(0, 5).join(', ')}${f.elsewhere.length > 5 ? ` (+${f.elsewhere.length - 5} more)` : ''}`);
    console.log('');
  }
  console.log('Retold fact: keep the telling where a change would falsify it; the rest point.');
}

function main() {
  const { base, skips } = parseArgs(process.argv.slice(2));
  const skipMatcher = buildSkipMatcher(skips);

  if (git(['rev-parse', '--verify', `${base}^{commit}`]) === null) {
    die(`base ref '${base}' does not resolve. Pass one explicitly, or fetch it first.`);
  }

  const diffNames = git(['diff', '--name-only', '-z', `${base}...HEAD`]);
  if (diffNames === null) die(`git diff against '${base}' failed.`);

  const changed = diffNames.split('\0').filter(f => f && !skipMatcher.test(f));
  if (changed.length === 0) {
    console.log('No changed files to check.');
    return;
  }

  const tracked = trackedPaths(skipMatcher);
  if (tracked === null) die('git ls-files failed.');

  const index = buildCommentIndex(tracked);
  if (index === null) die('git cat-file --batch failed.');

  const findings = [];
  for (const file of changed) {
    const diff = git(['diff', `${base}...HEAD`, '--', file]);
    if (diff === null) die(`git diff of '${file}' failed.`);
    findings.push(...findRetoldInDiff(diff, file, index));
  }

  report(dedupePairs(findings));
}

module.exports = { buildSkipMatcher, prose, buildCommentIndex, findRetoldInDiff, dedupePairs };

if (require.main === module) main();
