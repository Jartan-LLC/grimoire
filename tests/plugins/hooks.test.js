// The process contract every shipped hook keeps: whatever arrives on stdin, it
// exits 0 and prints nothing or exactly one JSON object. Every command entry in
// every plugins/*/hooks/hooks.json is run as Claude Code runs it, through a shell.

const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT, gitEnv, initRepo, tempDir, writeFiles } = require('../helpers/fixture');
const { knownDefect } = require('../helpers/known-defect');

const PLUGINS = path.join(REPO_ROOT, 'plugins');

// Contract breaks in shipped hooks, keyed "<plugin> <description>|<payload label or *>",
// each with the failure the defect produces.
const KNOWN_DEFECTS = {
  // The shell turns the \\ in [\/\\] into one backslash, so node -e fails to parse.
  'praxis Warn about non-standard documentation files|*': {
    issue: 'grimoire#76',
    expected: /^exit 1 .*SyntaxError: Invalid regular expression/s,
  },
};

// Hooks the large-context payload drives down their output path, so silence there
// means the hook stopped doing its job.
const SPEAKS_ON_LARGE_CONTEXT = new Set([
  'gitwise Load github-conventions for GitHub writes (gh pr/issue create/comment/edit, gh pr review, git commit/push/tag)',
  'gitwise Load commit-pr-writing on commit and PR text writes (git commit/push, gh pr create/edit)',
  'praxis Prompt the model to load the skills relevant to the task',
  'praxis Suggest manual compaction at logical intervals',
  'praxis Check for console.log in changed files after an edit',
]);

function hookEntries() {
  const entries = [];
  for (const plugin of fs.readdirSync(PLUGINS).sort()) {
    const manifest = path.join(PLUGINS, plugin, 'hooks', 'hooks.json');
    if (!fs.existsSync(manifest)) continue;
    const { hooks } = JSON.parse(fs.readFileSync(manifest, 'utf8'));
    for (const [event, groups] of Object.entries(hooks)) {
      for (const group of groups) {
        for (const hook of group.hooks) {
          if (hook.type !== 'command') continue;
          entries.push({ plugin, event, matcher: group.matcher, description: group.description, command: hook.command });
        }
      }
    }
  }
  return entries;
}

/** Payloads a hook must survive; the last ones are well-formed enough to reach each output path. */
function payloads(event, transcript) {
  const wellFormed = {
    session_id: 'contract-test',
    hook_event_name: event,
    source: 'compact',
    tool_name: 'Bash',
    tool_input: { command: 'git commit -m x && git push', file_path: 'notes.txt' },
  };
  return {
    'malformed JSON': '{"session_id": ',
    'empty input': '',
    'empty object': '{}',
    'valid JSON that is not an object': '[]',
    'valid JSON that is a string': '"x"',
    'fields of the wrong type': JSON.stringify({ session_id: 7, transcript_path: 7, hook_event_name: 7, tool_input: 'x' }),
    'missing transcript_path': JSON.stringify(wellFormed),
    'transcript_path to a large context': JSON.stringify({ ...wellFormed, transcript_path: transcript }),
  };
}

const PAYLOAD_LABELS = Object.keys(payloads('', ''));

/** A git checkout holding an untracked console.log, and a transcript past the context threshold. */
function workspace(t) {
  const cwd = initRepo(t, { 'README.md': 'fixture\n' });
  writeFiles(cwd, { 'src/debug.js': 'console.log("debug");\n' });
  const transcript = path.join(tempDir(t), 'session.jsonl');
  const usage = { input_tokens: 10, cache_read_input_tokens: 500000 };
  fs.writeFileSync(transcript, `${JSON.stringify({ type: 'assistant', message: { usage } })}\n`);
  return { cwd, transcript, scratch: tempDir(t) };
}

function assertContract(result) {
  assert.equal(result.error, undefined, String(result.error));
  assert.equal(result.status, 0, `exit ${result.status} (signal ${result.signal}); stderr: ${result.stderr}`);
  const stdout = result.stdout.trim();
  if (stdout === '') return;
  let parsed;
  assert.doesNotThrow(() => {
    parsed = JSON.parse(stdout);
  }, `stdout is not one JSON value: ${JSON.stringify(result.stdout)}`);
  assert.ok(parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed), `stdout is not a JSON object: ${stdout}`);
}

const entries = hookEntries();

test('finds hook entries to check', () => {
  assert.ok(entries.length > 0, 'no command hooks found under plugins/*/hooks/hooks.json');
});

// Both tables key on a hook's free-text description, which a rename leaves stale.
test('every hook named in KNOWN_DEFECTS and SPEAKS_ON_LARGE_CONTEXT exists', () => {
  const hooks = new Set(entries.map(entry => `${entry.plugin} ${entry.description}`));
  const named = [...Object.keys(KNOWN_DEFECTS).map(key => key.split('|')[0]), ...SPEAKS_ON_LARGE_CONTEXT];
  assert.deepEqual(named.filter(key => !hooks.has(key)), []);
});

for (const entry of entries) {
  const name = `${entry.plugin} ${entry.event} ${entry.matcher || '(no matcher)'}: ${entry.description}`;
  describe(name, () => {
    for (const label of PAYLOAD_LABELS) {
      const key = `${entry.plugin} ${entry.description}`;
      const speaks = label === 'transcript_path to a large context' && SPEAKS_ON_LARGE_CONTEXT.has(key);
      const defect = KNOWN_DEFECTS[`${key}|${label}`] || KNOWN_DEFECTS[`${key}|*`];
      const body = t => {
        const { cwd, transcript, scratch } = workspace(t);
        const pluginRoot = path.join(PLUGINS, entry.plugin);
        const result = spawnSync('sh', ['-c', entry.command], {
          cwd,
          input: payloads(entry.event, transcript)[label],
          encoding: 'utf8',
          timeout: 15000,
          env: gitEnv({
            PATH: process.env.PATH,
            HOME: scratch,
            TMPDIR: scratch,
            CLAUDE_PLUGIN_ROOT: pluginRoot,
            PLUGIN_ROOT: pluginRoot,
            CODEX_HOME: path.join(scratch, 'codex'),
            COMPACT_THRESHOLD: '1',
          }),
        });
        assertContract(result);
        if (speaks) assert.notEqual(result.stdout.trim(), '', 'expected output on this payload');
      };
      test(
        `exits 0 and prints ${speaks ? 'one JSON object' : 'nothing or one JSON object'} on ${label}`,
        defect ? knownDefect(defect.issue, defect.expected, body) : body,
      );
    }
  });
}
