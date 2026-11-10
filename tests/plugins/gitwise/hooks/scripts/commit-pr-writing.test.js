const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { describe, test } = require('node:test');

const { REPO_ROOT, tempDir } = require('../../../../helpers/fixture');

const SCRIPT = path.join(REPO_ROOT, 'plugins/gitwise/hooks/scripts/commit-pr-writing.js');
const { DENY_REASON, HINT, decide } = require(SCRIPT);

const SESSION = '30fcfb46-0dc1-4f2d-bf35-839e340d1630';
const MAIN = `/home/u/.claude/projects/-repo/${SESSION}.jsonl`;
const SKILL_DIR = '/home/u/.claude/plugins/cache/grimoire/gitwise/2.1.0/skills/commit-pr-writing';

// Record shapes as Claude Code 2.1.314-2.1.321 writes them to the transcript.
const prompt = { type: 'user', sessionId: SESSION, uuid: 'u-prompt', message: { role: 'user', content: 'Commit it.' } };
const skillCall = {
  type: 'assistant',
  sessionId: SESSION,
  uuid: 'u-call',
  message: { content: [{ type: 'tool_use', id: 'toolu_1', name: 'Skill', input: { skill: 'gitwise:commit-pr-writing' } }] },
};
const skillLaunched = {
  type: 'user',
  sessionId: SESSION,
  uuid: 'u-launched',
  message: { content: [{ type: 'tool_result', tool_use_id: 'toolu_1', content: 'Launching skill: gitwise:commit-pr-writing' }] },
  toolUseResult: { success: true, commandName: 'gitwise:commit-pr-writing' },
};
const skillBody = {
  type: 'user',
  isMeta: true,
  sessionId: SESSION,
  uuid: 'u-body',
  sourceToolUseID: 'toolu_1',
  message: { content: [{ type: 'text', text: `Base directory for this skill: ${SKILL_DIR}\n\n# Commit Messages and PR Descriptions\n` }] },
};
const skillFailed = {
  type: 'user',
  sessionId: SESSION,
  uuid: 'u-failed',
  message: {
    content: [{ type: 'tool_result', tool_use_id: 'toolu_1', is_error: true, content: 'Unknown skill: gitwise:commit-pr-writing' }],
  },
};
// An agent's `skills:` preload: no tool call, the command tags and the body in one record.
const preload = {
  type: 'user',
  isMeta: true,
  sessionId: SESSION,
  uuid: 'u-preload',
  message: {
    content: [
      { type: 'text', text: '<command-message>gitwise:commit-pr-writing</command-message>\n<command-name>gitwise:commit-pr-writing</command-name>' },
      { type: 'text', text: `Base directory for this skill: ${SKILL_DIR}\n\n# Commit Messages and PR Descriptions\n` },
    ],
  },
};
// The skill's text read back as a file, which does not put the skill in context as loaded.
const fileRead = {
  type: 'user',
  sessionId: SESSION,
  uuid: 'u-read',
  message: { content: [{ type: 'tool_result', tool_use_id: 'toolu_2', content: `Base directory for this skill: ${SKILL_DIR}` }] },
};
const earlierDeny = {
  type: 'user',
  sessionId: SESSION,
  uuid: 'u-deny',
  message: {
    content: [{ type: 'tool_result', tool_use_id: 'toolu_3', is_error: true, content: `PreToolUse:Bash hook error: ${DENY_REASON}` }],
  },
  permissionDecision: { decision: 'reject', source: 'hook', reasonType: 'hook', reasonCode: 'hook:PreToolUse' },
};
// A compaction as Claude Code 2.1.321 writes it: the boundary, the summary, then the
// re-injection of the skills invoked before it, which a resumed process leaves out.
const boundary = {
  parentUuid: null,
  logicalParentUuid: 'u-body',
  isSidechain: false,
  type: 'system',
  subtype: 'compact_boundary',
  content: 'Conversation compacted',
  isMeta: false,
  uuid: 'u-boundary',
  level: 'info',
  compactMetadata: { trigger: 'manual', preTokens: 22263, durationMs: 8311, postTokens: 6675 },
  sessionId: SESSION,
};
const summary = {
  parentUuid: 'u-boundary',
  isSidechain: false,
  type: 'user',
  message: { role: 'user', content: 'This session is being continued from a previous conversation that ran out of context.' },
  isVisibleInTranscriptOnly: true,
  isCompactSummary: true,
  uuid: 'u-summary',
  sessionId: SESSION,
};
const reinjected = (...names) => ({
  parentUuid: 'u-summary',
  isSidechain: false,
  attachment: {
    type: 'invoked_skills',
    skills: names.map(name => ({
      name,
      path: `plugin:${name}`,
      content: `Base directory for this skill: /home/u/.claude/plugins/cache/grimoire/${name.replace(':', '/')}\n\n# Body\n`,
    })),
  },
  type: 'attachment',
  uuid: 'u-reinjected',
  sessionId: SESSION,
});

const jsonl = records => `${records.map(r => JSON.stringify(r)).join('\n')}\n`;
const reader = files => file => (file in files ? Buffer.from(files[file]) : null);
const input = (command, extra = {}) => ({
  session_id: SESSION,
  transcript_path: MAIN,
  hook_event_name: 'PreToolUse',
  tool_name: 'Bash',
  tool_input: { command },
  ...extra,
});

const DENY = {
  hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: DENY_REASON },
};
const HINTED = { hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext: HINT } };

describe('which commands write text', () => {
  // With no load of the skill in the transcript, decide denies exactly the commands that write text.
  const unloaded = command => decide(input(command), reader({ [MAIN]: jsonl([prompt]) }));
  for (const command of [
    'git commit -m "feat: x"',
    'git add notes.txt && git commit -m "add notes"',
    'git add notes.txt; git commit -m "add notes"',
    '(cd /repo && git commit -m x)',
    'git commit --amend -m "fix: y"',
    'git commit --amend --no-edit -m "fix: y"',
    'git -C /repo commit -m x -- notes.txt',
    'git -c user.name=t commit -m x',
    'git --no-pager commit --amend',
    'git --git-dir /repo/.git commit -m x',
    'git -C "/a b" commit -m x',
    'git -c user.name="A B" commit -m x',
    'git --git-dir="/a b/.git" commit -m x',
    'printf "x\\n" | git commit -F -',
    'gh pr create --draft --title t --body-file b.md',
    'gh pr edit 5 --body-file b.md',
    'gh pr edit 5 -t "fix: y"',
    'gh pr edit 5 --title="fix: y"',
    'SKIP=ruff git commit -m x',
    'GIT_AUTHOR_NAME="A B" git commit -m x',
    'if true; then git commit -m x; fi',
    'if git commit -m x; then :; fi',
    'if false; then :; elif git commit -m x; then :; fi',
    'while git commit -m x; do :; done',
    'until git commit -m x; do :; done',
    'for f in a; do git commit -m x; done',
    'time git commit -m x',
    'env FOO=1 git commit -m x',
    'command git commit -m x',
    'exec git commit -m x',
    '! git commit -m x',
    '{ git commit -m x; }',
    'git commit -m "docs: document the -h flag"',
    "gh pr create --title 'add --help text'",
    'git commit -m "fix: accept -h\n\nBody."',
    'git -C /repo commit --amend',
    'git commit -c HEAD',
    'git commit --fixup=abc -m "why"',
    'git commit --fixup=amend:abc',
    'git commit --fixup reword:abc',
  ]) {
    test(`denies ${command}`, () => assert.deepEqual(unloaded(command), DENY));
  }
  for (const command of [
    'git push -u origin feature/x',
    'git commit-tree abc -m x',
    'git log --grep commit',
    'rg "git commit" plugins/',
    'git log --grep="git commit"',
    'echo "run gh pr create later"',
    'gh pr create --help',
    'git commit -h',
    'git commit --amend --no-edit',
    'gh pr edit 5 --add-label bug',
    'gh pr view 5',
    'echo commit',
    'FOO="git commit -m x" rg y',
    'domain git commit -m x',
    'gh pr edit 5 --add-label "needs -t triage"',
    'git commit --fixup=abc',
    'git commit --fixup abc',
    'git commit -C HEAD',
    'git commit --amend -C HEAD',
    'git commit --reuse-message=HEAD',
    'git -C /repo commit -C HEAD',
  ]) {
    test(`does not deny ${command}`, () => assert.notDeepEqual(unloaded(command), DENY));
  }
});

describe('decide', () => {
  test('prints nothing for a command that writes nothing', () => {
    assert.equal(decide(input('git status'), reader({ [MAIN]: jsonl([prompt]) })), null);
  });

  test('denies a commit when the transcript shows no load of the skill', () => {
    assert.deepEqual(decide(input('git add a && git commit -m x'), reader({ [MAIN]: jsonl([prompt]) })), DENY);
  });

  test('denies a PR create and a PR text edit the same way', () => {
    const read = reader({ [MAIN]: jsonl([prompt]) });
    assert.deepEqual(decide(input('gh pr create --title t --body b'), read), DENY);
    assert.deepEqual(decide(input('gh pr edit 3 --body-file b.md'), read), DENY);
  });

  test('prints nothing for a command that only names a commit in an argument', () => {
    assert.equal(decide(input('rg "git commit" plugins/'), reader({ [MAIN]: jsonl([prompt]) })), null);
  });

  test('only hints on a push, a commit that keeps or reuses a message, or a PR edit that carries no text', () => {
    const read = reader({ [MAIN]: jsonl([prompt]) });
    assert.deepEqual(decide(input('git push'), read), HINTED);
    assert.deepEqual(decide(input('git -C /repo push'), read), HINTED);
    assert.deepEqual(decide(input('git commit --amend --no-edit'), read), HINTED);
    assert.deepEqual(decide(input('git commit --fixup=abc'), read), HINTED);
    assert.deepEqual(decide(input('git commit --amend -C HEAD'), read), HINTED);
    assert.deepEqual(decide(input('gh pr create --help'), read), HINTED);
    assert.deepEqual(decide(input('gh pr edit 3 --add-label bug'), read), HINTED);
    assert.deepEqual(decide(input('env git push'), read), HINTED);
    assert.deepEqual(decide(input('git -C "/a b" push'), read), HINTED);
    assert.deepEqual(decide(input('git -C "/a b" commit -C HEAD'), read), HINTED);
  });

  test('allows once the Skill tool has injected the skill', () => {
    const read = reader({ [MAIN]: jsonl([prompt, skillCall, skillLaunched, skillBody]) });
    assert.deepEqual(decide(input('git commit -m x'), read), HINTED);
  });

  test('allows once an agent preload has injected the skill', () => {
    assert.deepEqual(decide(input('git commit -m x'), reader({ [MAIN]: jsonl([prompt, preload]) })), HINTED);
  });

  test('counts no load from a Skill call alone, a failed call, or the skill text read as a file', () => {
    const read = reader({ [MAIN]: jsonl([prompt, skillCall, skillFailed, fileRead]) });
    assert.deepEqual(decide(input('git commit -m x'), read), DENY);
  });

  test('denies once: after its own deny, the next write gets the hint', () => {
    assert.deepEqual(decide(input('git commit -m x'), reader({ [MAIN]: jsonl([prompt, earlierDeny]) })), HINTED);
  });

  test('fails open when there is no transcript_path or it cannot be read', () => {
    assert.deepEqual(decide(input('git commit -m x', { transcript_path: undefined }), reader({})), HINTED);
    assert.deepEqual(decide(input('git commit -m x'), reader({})), HINTED);
  });

  test('fails open on a transcript of another format or session, such as a Codex rollout', () => {
    const rollout = jsonl([{ timestamp: '2026-11-09T00:00:00Z', type: 'session_meta', payload: { id: SESSION } }]);
    assert.deepEqual(decide(input('git commit -m x'), reader({ [MAIN]: rollout })), HINTED);
    const other = jsonl([{ ...prompt, sessionId: 'another-session' }]);
    assert.deepEqual(decide(input('git commit -m x'), reader({ [MAIN]: other })), HINTED);
  });

  describe('after a compaction', () => {
    const loadedThenCompacted = [prompt, skillCall, skillLaunched, skillBody, boundary, summary];

    test('allows when Claude Code re-injected the skill', () => {
      const read = reader({ [MAIN]: jsonl([...loadedThenCompacted, reinjected('gitwise:commit-pr-writing')]) });
      assert.deepEqual(decide(input('git commit -m x'), read), HINTED);
    });

    test('denies when nothing was re-injected, as after a --resume', () => {
      assert.deepEqual(decide(input('git commit -m x'), reader({ [MAIN]: jsonl([...loadedThenCompacted, prompt]) })), DENY);
    });

    test('denies when the re-injection dropped the skill for newer ones', () => {
      const read = reader({
        [MAIN]: jsonl([...loadedThenCompacted, reinjected('praxis:comment-hygiene', 'pythonica:pydantic'), prompt]),
      });
      assert.deepEqual(decide(input('git commit -m x'), read), DENY);
    });

    test('allows once the skill is loaded again after it', () => {
      const read = reader({ [MAIN]: jsonl([...loadedThenCompacted, prompt, skillCall, skillLaunched, skillBody]) });
      assert.deepEqual(decide(input('git commit -m x'), read), HINTED);
    });

    test('denies once more, since a deny before the compaction no longer counts', () => {
      const deniedThenCompacted = [prompt, earlierDeny, boundary, summary, prompt];
      assert.deepEqual(decide(input('git commit -m x'), reader({ [MAIN]: jsonl(deniedThenCompacted) })), DENY);
      const deniedAgain = reader({ [MAIN]: jsonl([...deniedThenCompacted, earlierDeny]) });
      assert.deepEqual(decide(input('git commit -m x'), deniedAgain), HINTED);
    });
  });

  test('without a compaction, a load or deny anywhere in the transcript still counts', () => {
    const later = { ...prompt, uuid: 'u-later', message: { role: 'user', content: 'Now push it.' } };
    const loaded = reader({ [MAIN]: jsonl([prompt, skillCall, skillLaunched, skillBody, later]) });
    assert.deepEqual(decide(input('git commit -m x'), loaded), HINTED);
    assert.deepEqual(decide(input('git commit -m x'), reader({ [MAIN]: jsonl([prompt, earlierDeny, later]) })), HINTED);
  });

  describe('in a subagent', () => {
    const own = `/home/u/.claude/projects/-repo/${SESSION}/subagents/agent-a052e03751cd6f62f.jsonl`;
    const sub = command => input(command, { agent_id: 'a052e03751cd6f62f', agent_type: 'general-purpose' });

    test("reads the subagent's own transcript, not the main one's loads", () => {
      const read = reader({ [MAIN]: jsonl([prompt, skillBody]), [own]: jsonl([prompt]) });
      assert.deepEqual(decide(sub('git commit -m x'), read), DENY);
    });

    test('allows once the subagent loaded the skill itself', () => {
      const read = reader({ [MAIN]: jsonl([prompt]), [own]: jsonl([prompt, skillBody]) });
      assert.deepEqual(decide(sub('git commit -m x'), read), HINTED);
    });

    test('fails open when its transcript is missing or the agent id is not a plain id', () => {
      const read = reader({ [MAIN]: jsonl([prompt]) });
      assert.deepEqual(decide(sub('git commit -m x'), read), HINTED);
      assert.deepEqual(decide(input('git commit -m x', { agent_id: '../../etc' }), read), HINTED);
    });

    test('counts only what follows its own last compaction, not the main session\'s', () => {
      const sidechain = record => ({ ...record, isSidechain: true, agentId: 'a052e03751cd6f62f' });
      const compacted = [prompt, skillBody, boundary, summary].map(sidechain);
      assert.deepEqual(decide(sub('git commit -m x'), reader({ [MAIN]: jsonl([prompt]), [own]: jsonl(compacted) })), DENY);
      const kept = jsonl([...compacted, sidechain(reinjected('gitwise:commit-pr-writing'))]);
      assert.deepEqual(decide(sub('git commit -m x'), reader({ [MAIN]: jsonl([prompt]), [own]: kept })), HINTED);
      const mainCompacted = jsonl([prompt, boundary, summary]);
      assert.deepEqual(decide(sub('git commit -m x'), reader({ [MAIN]: mainCompacted, [own]: jsonl([prompt, skillBody]) })), HINTED);
    });

    test("a fork counts the main session's loads up to where it forked", () => {
      const fork = { type: 'fork-context-ref', agentId: 'a052e03751cd6f62f', parentSessionId: SESSION };
      const forkedAfterLoad = jsonl([{ ...fork, parentLastUuid: 'u-body' }, prompt]);
      const forkedBeforeLoad = jsonl([{ ...fork, parentLastUuid: 'u-prompt' }, prompt]);
      const main = jsonl([prompt, skillBody]);
      assert.deepEqual(decide(sub('git commit -m x'), reader({ [MAIN]: main, [own]: forkedAfterLoad })), HINTED);
      assert.deepEqual(decide(sub('git commit -m x'), reader({ [MAIN]: main, [own]: forkedBeforeLoad })), DENY);
    });

    describe('a fork after a compaction', () => {
      const fork = { type: 'fork-context-ref', agentId: 'a052e03751cd6f62f', parentSessionId: SESSION };
      const later = { ...prompt, uuid: 'u-later', message: { role: 'user', content: 'Now fork.' } };
      const sidechain = record => ({ ...record, isSidechain: true, agentId: 'a052e03751cd6f62f' });

      test('stops at its own compaction, not reaching back to the parent\'s load', () => {
        const read = reader({
          [MAIN]: jsonl([prompt, skillBody]),
          [own]: jsonl([{ ...fork, parentLastUuid: 'u-body' }, ...[prompt, boundary, summary, prompt].map(sidechain)]),
        });
        assert.deepEqual(decide(sub('git commit -m x'), read), DENY);
      });

      test("counts the parent's history only after the parent's last compaction", () => {
        const read = reader({
          [MAIN]: jsonl([prompt, skillBody, boundary, summary, later]),
          [own]: jsonl([{ ...fork, parentLastUuid: 'u-later' }, prompt]),
        });
        assert.deepEqual(decide(sub('git commit -m x'), read), DENY);
      });

      test("counts a parent's load made after the parent's compaction", () => {
        const read = reader({
          [MAIN]: jsonl([prompt, boundary, summary, skillBody]),
          [own]: jsonl([{ ...fork, parentLastUuid: 'u-body' }, prompt]),
        });
        assert.deepEqual(decide(sub('git commit -m x'), read), HINTED);
      });
    });
  });
});

test('the entry point reads the transcript from disk and prints the deny', t => {
  const transcript = path.join(tempDir(t), `${SESSION}.jsonl`);
  fs.writeFileSync(transcript, jsonl([prompt]));
  const result = spawnSync('node', [SCRIPT], {
    input: JSON.stringify({ ...input('git commit -m x'), transcript_path: transcript }),
    encoding: 'utf8',
  });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout), DENY);
});
