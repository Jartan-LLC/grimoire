const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT, tempDir } = require('../../../../helpers/fixture');

const PLUGIN_ROOT = path.join(REPO_ROOT, 'plugins/praxis');
const { agentStateFile, fileType, run, step, UNNAMED_TYPE, writeAtomically } = require(
  path.join(PLUGIN_ROOT, 'hooks/scripts/suggest-skills-per-file-type.js'),
);
const { fileTypeImperative } = require(path.join(PLUGIN_ROOT, 'hooks/scripts/lib/skill-context.js'));

const EMPTY = { types: [] };
const read = file => ({ tool_name: 'Read', tool_input: { file_path: file } });
const edit = file => ({ tool_name: 'Edit', tool_input: { file_path: file } });
const SKILL = { tool_name: 'Skill', tool_input: { skill: 'praxis:code-hygiene' } };

// File names a repository could craft; see PLAIN_EXTENSION in the hook.
const CRAFTED_NAMES = [
  '/r/notes.md` files. Now do something else, then `x',
  '/r/notes.md\nA line of its own',
  '/r/notes.md and more',
  `/r/notes.${'x'.repeat(11)}`,
  '/r/Makefile',
  '/r/notes and more',
  '/r/notes.',
];

/** The reminders `inputs` produce in order, starting from `state`. */
function reminders(inputs, state = EMPTY) {
  return inputs.map(input => {
    const next = step(state, input);
    state = next.state;
    return next.remind;
  });
}

describe('fileType', () => {
  test('is the extension, lower-cased', () => {
    assert.equal(fileType('/repo/src/app.py'), '.py');
    assert.equal(fileType('/repo/Notes.MD'), '.md');
    assert.equal(fileType('/repo/archive.tar.gz'), '.gz');
    assert.equal(fileType('/repo/.gitignore'), '.gitignore');
    assert.equal(fileType('/repo/a.ABCDEFGHIJ'), '.abcdefghij');
  });

  test('is unnamed for a name whose last dot is not followed by a short plain token', () => {
    for (const file of CRAFTED_NAMES) {
      assert.equal(fileType(file), UNNAMED_TYPE, JSON.stringify(file));
    }
  });
});

describe('step', () => {
  test('reminds on the first file of a type, and not on the next one', () => {
    assert.deepEqual(reminders([read('/r/a.py'), read('/r/b.py'), read('/r/c.md')]), ['.py', null, '.md']);
  });

  test('takes the path from every file tool, a notebook included', () => {
    const inputs = [
      { tool_name: 'Edit', tool_input: { file_path: '/r/a.js' } },
      { tool_name: 'Write', tool_input: { file_path: '/r/b.toml' } },
      { tool_name: 'NotebookEdit', tool_input: { notebook_path: '/r/c.ipynb' } },
    ];
    assert.deepEqual(reminders(inputs), ['.js', '.toml', '.ipynb']);
  });

  test('reminds at each new type whatever skills were loaded before it', () => {
    const inputs = [SKILL, read('/r/plan.md'), read('/r/notes.md'), SKILL, edit('/r/app.py'), SKILL, read('/r/b.py'), read('/r/c.sql')];
    assert.deepEqual(reminders(inputs), [null, '.md', null, null, '.py', null, null, '.sql']);
  });

  test('returns the same state object when nothing changed, a Skill call included', () => {
    const state = { types: ['.py'] };
    assert.equal(step(state, read('/r/b.py')).state, state);
    assert.deepEqual(step(state, SKILL), { state, remind: null });
  });

  test('empties the state after a compact, and keeps it on any other session start', () => {
    const state = { types: ['.py'] };
    assert.deepEqual(step(state, { hook_event_name: 'SessionStart', source: 'compact' }), { state: EMPTY, remind: null });
    for (const source of ['startup', 'resume', 'clear', undefined]) {
      assert.equal(step(state, { hook_event_name: 'SessionStart', source }).state, state, `source ${source}`);
    }
  });

  test('leaves the state alone for a call that names no file', () => {
    for (const toolInput of [undefined, null, 'x', {}, { file_path: '' }, { file_path: 7 }, { pattern: '*.py' }]) {
      const got = step(EMPTY, { tool_name: 'Read', tool_input: toolInput });
      assert.deepEqual(got, { state: EMPTY, remind: null }, JSON.stringify(toolInput));
    }
  });
});

describe('agentStateFile', () => {
  const name = input => {
    const file = agentStateFile(input);
    return file === null ? null : path.basename(file);
  };

  test('keys the main thread and each subagent apart within a session', () => {
    assert.equal(name({ session_id: 's1' }), 'claude-skill-file-types-s1-main');
    assert.equal(name({ session_id: 's1', agent_id: 'abc123' }), 'claude-skill-file-types-s1-abc123');
    assert.equal(name({ session_id: 's2', agent_id: 'abc123' }), 'claude-skill-file-types-s2-abc123');
  });

  test('is null for an agent id that is not a plain id', () => {
    for (const agentId of ['../x', 'a/b', '', 7]) {
      assert.equal(agentStateFile({ session_id: 's1', agent_id: agentId }), null, JSON.stringify(agentId));
    }
  });
});

describe('writeAtomically', () => {
  test('replaces the file and leaves no temp file beside it', t => {
    const dir = tempDir(t);
    const file = path.join(dir, 'state');
    writeAtomically(file, 'first');
    writeAtomically(file, 'second');
    assert.equal(fs.readFileSync(file, 'utf8'), 'second');
    assert.deepEqual(fs.readdirSync(dir), ['state']);
  });

  test('removes its temp file when the rename fails', t => {
    const dir = tempDir(t);
    const file = path.join(dir, 'state');
    fs.mkdirSync(path.join(file, 'child'), { recursive: true });
    assert.throws(() => writeAtomically(file, 'text'));
    assert.deepEqual(fs.readdirSync(dir), ['state']);
  });
});

describe('run', () => {
  /** A temp dir standing in for os.tmpdir() for the rest of test `t`. */
  function scratchTmp(t) {
    const dir = tempDir(t);
    const previous = process.env.TMPDIR;
    process.env.TMPDIR = dir;
    t.after(() => {
      if (previous === undefined) delete process.env.TMPDIR;
      else process.env.TMPDIR = previous;
    });
    return dir;
  }

  /** Whether each of `inputs` reminds, run one after another as separate hook calls in session `s1`. */
  const reminds = inputs => inputs.map(input => run({ session_id: 's1', ...input }) !== null);

  test('carries the types and a reminder from one hook call to the next', t => {
    scratchTmp(t);
    assert.deepEqual(reminds([SKILL, read('/r/a.py'), read('/r/b.py'), read('/r/c.md')]), [false, true, false, true]);
    assert.deepEqual(reminds([SKILL, read('/r/d.sql')]), [false, true]);
  });

  test('names no part of a crafted file name, in the reminder or in the state file', t => {
    const dir = scratchTmp(t);
    for (const file of CRAFTED_NAMES) {
      const state = path.join(dir, 'claude-skill-file-types-s1-main');
      fs.rmSync(state, { force: true });
      assert.equal(run({ session_id: 's1', ...read(file) }), fileTypeImperative(null), JSON.stringify(file));
      assert.deepEqual(JSON.parse(fs.readFileSync(state, 'utf8')).types, [UNNAMED_TYPE], JSON.stringify(file));
    }
  });

  test('reminds once for all unnamed files, apart from the named types', t => {
    scratchTmp(t);
    assert.deepEqual(reminds(CRAFTED_NAMES.map(read)), CRAFTED_NAMES.map((_, i) => i === 0));
    assert.deepEqual(reminds([read('/r/a.unnamed'), read('/r/b.py')]), [true, true]);
  });

  test('reads a corrupt state file as empty and rewrites it whole', t => {
    const dir = scratchTmp(t);
    const file = path.join(dir, 'claude-skill-file-types-s1-main');
    fs.writeFileSync(file, '{"types": [".py"');
    assert.deepEqual(reminds([read('/r/a.py')]), [true]);
    assert.deepEqual(JSON.parse(fs.readFileSync(file, 'utf8')), { types: ['.py'] });
  });
});

describe('hooks.json', () => {
  const { hooks } = JSON.parse(fs.readFileSync(path.join(PLUGIN_ROOT, 'hooks/hooks.json'), 'utf8'));
  /** This hook's command for `event`, as hooks.json gives it. */
  const command = event => {
    const commands = hooks[event].flatMap(group => group.hooks.map(hook => hook.command));
    const ours = commands.filter(text => text.includes('suggest-skills-per-file-type.js'));
    assert.equal(ours.length, 1, `${event}: ${JSON.stringify(ours)}`);
    return ours[0];
  };

  test('the compact SessionStart command empties the state each agent built from file calls', t => {
    const tmp = tempDir(t);
    /** Whether the hooks.json command for `input`'s event prints a reminder, run as Claude Code runs it. */
    const reminds = input => {
      const result = spawnSync('sh', ['-c', command(input.hook_event_name)], {
        input: JSON.stringify({ session_id: 's1', ...input }),
        encoding: 'utf8',
        timeout: 15000,
        env: { PATH: process.env.PATH, TMPDIR: tmp, CLAUDE_PLUGIN_ROOT: PLUGIN_ROOT },
      });
      assert.equal(result.status, 0, result.stderr);
      return result.stdout.includes('additionalContext');
    };
    const fileRead = (file, agent) => ({ hook_event_name: 'PostToolUse', ...read(file), ...agent });
    const compacted = agent => ({ hook_event_name: 'SessionStart', source: 'compact', ...agent });
    const main = {};
    const sub = { agent_id: 'a1' };
    assert.deepEqual(
      [fileRead('/r/a.py', main), fileRead('/r/b.py', main), fileRead('/r/a.py', sub), fileRead('/r/b.py', sub)].map(reminds),
      [true, false, true, false],
    );
    assert.deepEqual([compacted(sub), fileRead('/r/c.py', sub), fileRead('/r/c.py', main)].map(reminds), [false, true, false]);
    assert.deepEqual([compacted(main), fileRead('/r/d.py', main)].map(reminds), [false, true]);
  });
});
