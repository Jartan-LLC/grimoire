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

/** Reduce a comment line to comparable prose, or '' when it carries none. */
function prose(line) {
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

function main() {
  const { base, skips } = parseArgs(process.argv.slice(2));
  const skipPaths = buildSkipMatcher(skips);

  if (git(['rev-parse', '--verify', `${base}^{commit}`]) === null) {
    die(`base ref '${base}' does not resolve. Pass one explicitly, or fetch it first.`);
  }

  const diffNames = git(['diff', '--name-only', `${base}...HEAD`]);
  if (diffNames === null) die(`git diff against '${base}' failed.`);

  const changed = diffNames.split('\n').filter(f => f && !skipPaths.test(f));
  if (changed.length === 0) {
    console.log('No changed files to check.');
    return;
  }

  // Index every comment in the tracked tree, so a retelling is found whether or
  // not the other site was touched by this change.
  const index = new Map();
  const tracked = git(['ls-files']);
  if (tracked === null) die('git ls-files failed.');

  for (const file of tracked.split('\n')) {
    if (!file || skipPaths.test(file)) continue;
    const content = git(['show', `HEAD:${file}`]);
    // Absent from HEAD (newly added) is normal; a read failure is not, but
    // cannot be told apart here -- either way there is nothing to index.
    if (content === null || content === '') continue;
    content.split('\n').forEach((line, i) => {
      const text = prose(line);
      if (!text) return;
      if (!index.has(text)) index.set(text, []);
      index.get(text).push(`${file}:${i + 1}`);
    });
  }

  const findings = [];
  // When both sides of a retelling are added in the same diff, each side finds
  // the other; without this the reviewer reads every such pair twice.
  const reported = new Set();

  for (const file of changed) {
    const diff = git(['diff', `${base}...HEAD`, '--', file]);
    if (diff === null) die(`git diff of '${file}' failed.`);
    let lineNo = 0;
    for (const line of diff.split('\n')) {
      const hunk = line.match(/^@@ -\d+(?:,\d+)? \+(\d+)/);
      if (hunk) { lineNo = parseInt(hunk[1], 10); continue; }
      if (line.startsWith('-')) continue;
      if (!line.startsWith('+')) { lineNo++; continue; }

      const text = prose(line.slice(1));
      const here = `${file}:${lineNo}`;
      lineNo++;
      if (!text) continue;

      const elsewhere = (index.get(text) || []).filter(site => site !== here);
      if (elsewhere.length === 0) continue;

      const pairKey = [here, ...elsewhere].sort().join('|');
      if (reported.has(pairKey)) continue;
      reported.add(pairKey);

      findings.push({ here, text, elsewhere });
    }
  }

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

main();
