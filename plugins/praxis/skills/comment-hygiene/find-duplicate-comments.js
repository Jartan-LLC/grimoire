#!/usr/bin/env node
/**
 * Duplicate-comment finder.
 *
 * It runs against whatever repo is being reviewed, which is not this one. Keep
 * it free of assumptions about this repo's layout: a rule that suppresses a
 * finding here silently suppresses real ones in every repo praxis reviews.
 *
 * The Retold fact rule cannot be applied from one file: judging a comment as a
 * retelling means knowing whether the same fact is told elsewhere, which
 * per-file review structurally cannot see. This supplies that whole-repo view,
 * scoped by default to the diff -- comment lines ADDED by the change whose prose
 * already appears somewhere in the repo, naming both sites so the reviewer picks
 * a keeper.
 *
 * Usage:
 *   node find-duplicate-comments.js [base-ref] [--worktree] [--skip <segment>]...
 *   node find-duplicate-comments.js --all [--worktree] [--skip <segment>]...
 *
 *   base-ref    defaults to origin/main. Without --worktree, the comment lines
 *               committed since it (git diff base-ref...HEAD) are checked against
 *               every tracked file as committed at HEAD.
 *   --worktree  read the working tree instead of HEAD: also check the comment
 *               lines added by uncommitted changes, staged or not, and by
 *               untracked files git does not ignore, and match them against
 *               every file there, untracked ones included. A duplicate fixed but
 *               not yet committed stops reporting.
 *   --all       check every comment line, not only those added since a base, for
 *               a whole-repo sweep. Takes no base-ref.
 *   --skip      extra path segments to ignore, repeatable and matched literally.
 *               node_modules is always skipped; add generated trees here, e.g.
 *               --skip dist --skip build
 */

const fs = require('fs');
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
  let worktree = false;
  let all = false;

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--worktree') {
      worktree = true;
    } else if (arg === '--all') {
      all = true;
    } else if (arg === '--skip') {
      const value = argv[++i];
      if (!value) return die('--skip needs a pattern');
      skips.push(value);
    } else if (arg.startsWith('--skip=')) {
      skips.push(arg.slice('--skip='.length));
    } else if (arg.startsWith('-')) {
      return die(`unknown option '${arg}'`);
    } else if (base === null) {
      base = arg;
    } else {
      return die(`unexpected argument '${arg}'`);
    }
  }

  // A base beside --all would be silently ignored, and the run read as scoped to it.
  if (all && base !== null) return die('--all checks every comment and takes no base ref');
  return { base: all ? null : base || 'origin/main', skips, worktree, all };
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
 * Paths git tracks, each once, minus submodule gitlinks and skipped trees, or
 * null when git failed.
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

  // A Set, because an unresolved merge lists a conflicted path once per stage.
  const paths = new Set();
  for (const record of raw.split('\0')) {
    if (!record) continue;
    // `<mode> <sha> <stage>\t<path>`; a path may itself hold spaces or tabs, so
    // take it whole after the first tab and read the mode before the first space.
    const path = record.slice(record.indexOf('\t') + 1);
    const mode = record.slice(0, record.indexOf(' '));
    if (mode === '160000' || skipMatcher.test(path)) continue;
    paths.add(path);
  }
  return [...paths];
}

/**
 * Untracked paths git does not ignore, minus skipped trees, or null when git
 * failed. A nested repository is listed as its directory, which the worktree
 * reader passes over.
 */
function untrackedPaths(skipMatcher) {
  const raw = git(['ls-files', '--others', '--exclude-standard', '-z']);
  if (raw === null) return null;
  return raw.split('\0').filter(path => path && !skipMatcher.test(path));
}

/**
 * Contents of `files` at HEAD, positionally, with null for a path missing there;
 * null overall when git failed.
 *
 * One `git cat-file --batch` rather than a `git show` per file: this runs
 * against arbitrary repos, where per-file spawns scale with the checkout.
 */
function readAtHead(files) {
  return gitBatch(files.map(f => `HEAD:${f}`));
}

/**
 * Contents of `files` in the working tree, positionally, with null for a path
 * deleted there or that is not a regular file -- at HEAD a symlink's blob is its
 * target path, never comments. Null overall on any other read error: a file
 * dropped from the index unseen would make a clean result false.
 */
function readWorktree(files) {
  const contents = [];
  for (const file of files) {
    try {
      contents.push(fs.lstatSync(file).isFile() ? fs.readFileSync(file, 'utf8') : null);
    } catch (err) {
      if (err.code !== 'ENOENT' && err.code !== 'ENOTDIR') return null;
      contents.push(null);
    }
  }
  return contents;
}

/**
 * Map every comment's prose to the sites that carry it, across the whole tree as
 * `read` sees it -- a retelling counts whether or not the other site was touched
 * here. Null when reading failed.
 */
function buildCommentIndex(files, read = readAtHead) {
  if (files.length === 0) return new Map();

  const contents = read(files);
  return contents === null ? null : addToIndex(new Map(), files, contents);
}

/** Add the comments of `contents`, positional with `files`, to `index` and return it. */
function addToIndex(index, files, contents) {
  files.forEach((file, i) => {
    const content = contents[i];
    // No content where read (added since HEAD, deleted, or not a regular file) is
    // normal -- nothing to index.
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

/** A whole new file as the diff that adds it, for findRetoldInDiff. */
function addedFileDiff(content) {
  return '@@ -0,0 +1 @@\n' + content.split('\n').map(line => `+${line}`).join('\n');
}

/** Every prose told at more than one site, reported once from its first site. */
function findRepeated(index) {
  const findings = [];
  for (const [text, sites] of index) {
    if (sites.length > 1) findings.push({ here: sites[0], text, elsewhere: sites.slice(1) });
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

function report(findings, { all, worktree }) {
  if (findings.length === 0) {
    const scope = all ? '' : worktree ? ' in the diff or untracked files' : ' in the diff';
    console.log(`No retold comments found${scope}.`);
    return;
  }

  console.log(all
    ? `${findings.length} comment(s) told at more than one site:\n`
    : `${findings.length} added comment line(s) already told elsewhere:\n`);
  for (const f of findings) {
    console.log(`  ${f.here}`);
    console.log(`    "${f.text}"`);
    console.log(`    also at: ${f.elsewhere.slice(0, 5).join(', ')}${f.elsewhere.length > 5 ? ` (+${f.elsewhere.length - 5} more)` : ''}`);
    console.log('');
  }
  console.log('Retold fact: keep the telling where a change would falsify it; the rest point.');
}

function main() {
  const { base, skips, worktree, all } = parseArgs(process.argv.slice(2));
  const skipMatcher = buildSkipMatcher(skips);

  // `ls-files` lists paths and `diff` reads pathspecs from the current directory,
  // while `HEAD:<path>` and `diff --name-only` work from the top level. Run from a
  // subdirectory, the lookups at HEAD and the per-file diffs would miss, and a run
  // would report clean or cover only that subtree.
  const top = git(['rev-parse', '--show-toplevel']);
  if (top === null) return die('not inside a git working tree.');
  process.chdir(top.replace(/\n$/, ''));

  // Without --all, resolve the diff first: no changed files means no index to build.
  let range = null;
  let changed = [];
  if (!all) {
    if (git(['rev-parse', '--verify', `${base}^{commit}`]) === null) {
      return die(`base ref '${base}' does not resolve. Pass one explicitly, or fetch it first.`);
    }

    // `base...HEAD` diffs two commits; the working tree is reached only by
    // naming the merge base alone, which compares it with the working tree.
    if (worktree) {
      const mergeBase = git(['merge-base', base, 'HEAD']);
      if (mergeBase === null) return die(`'${base}' and HEAD share no merge base.`);
      range = mergeBase.trim();
    } else {
      range = `${base}...HEAD`;
    }

    const diffNames = git(['diff', '--name-only', '-z', range]);
    if (diffNames === null) return die(`git diff against '${base}' failed.`);
    changed = diffNames.split('\0').filter(f => f && !skipMatcher.test(f));
  }

  const untracked = worktree ? untrackedPaths(skipMatcher) : [];
  if (untracked === null) return die('git ls-files --others failed.');
  if (!all && changed.length === 0 && untracked.length === 0) {
    console.log('No changed files to check.');
    return;
  }

  const tracked = trackedPaths(skipMatcher);
  if (tracked === null) return die('git ls-files failed.');

  const index = buildCommentIndex(tracked, worktree ? readWorktree : readAtHead);
  const untrackedContents = index === null ? null : readWorktree(untracked);
  if (untrackedContents === null) {
    return die(worktree ? 'reading the working tree failed.' : 'git cat-file --batch failed.');
  }
  addToIndex(index, untracked, untrackedContents);

  if (all) {
    report(findRepeated(index), { all, worktree });
    return;
  }

  const findings = [];
  for (const file of changed) {
    const diff = git(['diff', range, '--', file]);
    if (diff === null) return die(`git diff of '${file}' failed.`);
    findings.push(...findRetoldInDiff(diff, file, index));
  }
  untracked.forEach((file, i) => {
    if (untrackedContents[i] !== null) {
      findings.push(...findRetoldInDiff(addedFileDiff(untrackedContents[i]), file, index));
    }
  });

  report(dedupePairs(findings), { all, worktree });
}

module.exports = { parseArgs, buildSkipMatcher, prose, buildCommentIndex, findRetoldInDiff, dedupePairs };

if (require.main === module) main();
