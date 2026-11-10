#!/usr/bin/env node
/**
 * Hold an agent's first commit or PR text write until commit-pr-writing is loaded.
 *
 * A PreToolUse hint reaches the model with the command's result, after the message it
 * was meant to shape is already written into the command and committed. So when this
 * agent's transcript shows no load of the skill, the write is denied once, with a
 * reason telling the agent to load it and write the message again.
 *
 * The deny fails open: with no readable Claude Code transcript (Codex, a moved file, a
 * changed format) the hook only adds the hint. A gate that fired on a read error would
 * block every commit with no way out but disabling the plugin. One deny per agent at
 * most between compactions, so a transcript that lags the conversation costs a turn,
 * never a lockout.
 *
 * A compaction drops the skill from context unless Claude Code re-injects it, which it
 * does not in a process started with `--resume`, or when newer skills fill the budget
 * for re-injected skills. So only a load, a re-injection or a deny since the agent's
 * last compaction counts.
 */

const fs = require('fs');

const HINT = 'Load the gitwise:commit-pr-writing skill.';
// Found again in the transcript to tell that this agent was already denied once.
const DENY_MARKER = 'Not run: load the gitwise:commit-pr-writing skill';
const DENY_REASON =
  `${DENY_MARKER}, then write the commit message or PR text again under it and reissue the whole ` +
  'command. Nothing in this command ran, including any step chained before the commit or PR write.';

// Global options such as `-C <dir>` may sit between `git` and its subcommand.
const GIT = String.raw`^git(?:\s+(?:-[cC]\s+\S+|--[\w-]+(?:[=\s]\S+)?))*\s+`;
const COMMIT = new RegExp(`${GIT}commit(?![\\w-])`);
const PUSH = new RegExp(`${GIT}push(?![\\w-])`);
const PR_CREATE = /^gh\s+pr\s+create\b/;
const PR_EDIT = /^gh\s+pr\s+edit\b/;
// The hint goes to every commit, push and PR create or edit, whether or not it writes text.
const HINTED = [COMMIT, PUSH, PR_CREATE, PR_EDIT];
const PR_TEXT_FLAG = /\s(?:--title|--body|--body-file|-[tbF])(?:[\s=]|$)/;
const HELP = /\s(?:--help|-h)(?:\s|$)/;
const NO_EDIT = /\s--no-edit(?:\s|$)/;
// Options that take an earlier commit's message; `--fixup=amend:` and `reword:` write a new one.
const REUSED_MESSAGE = /\s(?:-[a-zA-Z]*C|--reuse-message\b|--fixup(?![=\s](?:amend|reword):)(?:[=\s]|$))/;
const MESSAGE_FLAG = /\s(?:-[a-zA-Z]*[mF]|--message\b|--file\b)/;
// Words that run the command after them: assignments such as `SKIP=x`, keywords, wrappers.
const PREFIX =
  /^(?:[A-Za-z_]\w*=\S*|if|elif|while|until|then|do|else|time|env|command|exec|sudo|nohup|nice|timeout\s+\S+|!|\{)\s+/;
// A quoted string, or an unclosed one running to the end of a line of a multi-line message.
const QUOTED = /"[^"]*(?:"|$)|'[^']*(?:'|$)/g;
const SKILL_NAME = 'commit-pr-writing';
const SKILL_BODY_PREFIX = 'Base directory for this skill: ';
const SKILL_BODY = /^Base directory for this skill: .*[\\/]commit-pr-writing\s*$/m;
const REINJECTED_NAME = /(?:^|:)commit-pr-writing$/;
const COMPACT_BOUNDARY = '"subtype":"compact_boundary"';

/**
 * The simple commands in shell `command`, split at control operators, with quoted text
 * blanked to `""` and leading `PREFIX` words stripped, so that a phrase inside an
 * argument (`rg "git commit"`) is not taken for a command. Blanking lets `git -C "/a b"`
 * read as one option, and a message that names `-h` read as no help call. The split does
 * not parse quotes: a line of a quoted message or heredoc counts as a command of its own,
 * and a command run as a string, as in `bash -c "git commit -m x"`, is not seen.
 */
function commands(command) {
  return command.split(/[;&|\n(`]/).map(part => {
    let rest = part.trim().replace(QUOTED, '""');
    while (PREFIX.test(rest)) rest = rest.replace(PREFIX, '');
    return rest;
  });
}

/** Whether simple command `part`, from `commands`, writes a commit message or a PR title or body. */
function writes(part) {
  if (HELP.test(part)) return false;
  if (COMMIT.test(part)) {
    // Read past `commit`, as a global `git -C <dir>` sits before it.
    const options = part.replace(COMMIT, ' ');
    return MESSAGE_FLAG.test(options) || !(NO_EDIT.test(options) || REUSED_MESSAGE.test(options));
  }
  if (PR_CREATE.test(part)) return true;
  return PR_EDIT.test(part) && PR_TEXT_FLAG.test(part);
}

function textBlocks(content) {
  if (typeof content === 'string') return [content];
  if (!Array.isArray(content)) return [];
  return content.map(block => (block && typeof block.text === 'string' ? block.text : '')).filter(Boolean);
}

/** The skill's body injected into context: by the Skill tool, an agent's `skills:` or a slash command. */
function isSkillLoad(record) {
  if (record.type !== 'user' || record.isMeta !== true) return false;
  return textBlocks(record.message?.content).some(text => SKILL_BODY.test(text));
}

/** Claude Code's re-injection of invoked skills after a compaction, when it names this skill. */
function isReinjection(record) {
  if (record.type !== 'attachment' || record.attachment?.type !== 'invoked_skills') return false;
  const skills = record.attachment.skills;
  return Array.isArray(skills) && skills.some(skill => typeof skill?.name === 'string' && REINJECTED_NAME.test(skill.name));
}

function isOwnDeny(record) {
  const content = record.type === 'user' ? record.message?.content : null;
  if (!Array.isArray(content)) return false;
  return content.some(block => {
    if (block?.type !== 'tool_result' || block.is_error !== true) return false;
    return textBlocks(block.content).some(text => text.includes(DENY_MARKER));
  });
}

/** Where the line of `buf` holding byte `at` starts and ends, its newline left out. */
function lineAt(buf, at) {
  const newline = buf.indexOf(0x0a, at);
  return { start: buf.lastIndexOf(0x0a, at) + 1, end: newline < 0 ? buf.length : newline };
}

/** The record on the line of JSONL `buf` from `start` to `end`, or null. */
function parseLine(buf, start, end) {
  try {
    const record = JSON.parse(buf.toString('utf8', start, end));
    return record && typeof record === 'object' ? record : null;
  } catch {
    // A partial last line: the transcript is written while the session runs.
    return null;
  }
}

/**
 * Whether transcript JSONL `buf` shows a load or re-injection of the skill or this hook's earlier deny.
 * Transcripts run to hundreds of megabytes, past the longest string Node can hold, so
 * the search stays on the Buffer and parses only the lines that name the skill.
 */
function cleared(buf) {
  for (let at = buf.indexOf(SKILL_NAME); at >= 0; ) {
    const { start, end } = lineAt(buf, at);
    const line = buf.toString('utf8', start, end);
    if (line.includes(SKILL_BODY_PREFIX) || line.includes(DENY_MARKER) || line.includes('"invoked_skills"')) {
      const record = parseLine(buf, start, end);
      if (record && (isSkillLoad(record) || isReinjection(record) || isOwnDeny(record))) return true;
    }
    at = buf.indexOf(SKILL_NAME, end);
  }
  return false;
}

/** `buf` from its last compaction boundary on, or null when it has none. */
function sinceLastCompaction(buf) {
  for (let from = buf.length; from > 0; ) {
    const at = buf.lastIndexOf(COMPACT_BOUNDARY, from - 1);
    if (at < 0) return null;
    const { start, end } = lineAt(buf, at);
    const record = parseLine(buf, start, end);
    if (record?.type === 'system' && record.subtype === 'compact_boundary') return buf.subarray(start);
    from = at;
  }
  return null;
}

/**
 * Whether the agent's context, from `transcripts` read in order, has cleared the write
 * since its last compaction, which may sit in any of them.
 */
function clearedSinceCompaction(transcripts) {
  for (let i = transcripts.length - 1; i >= 0; i--) {
    const since = sinceLastCompaction(transcripts[i]);
    if (cleared(since ?? transcripts[i])) return true;
    if (since !== null) return false;
  }
  return false;
}

/** Whether `buf` is a Claude Code transcript of session `sessionId`. */
function isSessionTranscript(buf, sessionId) {
  return typeof sessionId === 'string' && sessionId !== '' && buf.includes(`"sessionId":${JSON.stringify(sessionId)}`);
}

/** `buf` up to the end of the record with `uuid`, or an empty Buffer when absent. */
function historyUpTo(buf, uuid) {
  const at = typeof uuid === 'string' && uuid !== '' ? buf.indexOf(`"uuid":${JSON.stringify(uuid)}`) : -1;
  return at < 0 ? Buffer.alloc(0) : buf.subarray(0, lineAt(buf, at).end);
}

/** The first record of JSONL `buf`, or null. */
function firstRecord(buf) {
  return parseLine(buf, 0, lineAt(buf, 0).end);
}

/**
 * The transcripts that make up the context of the agent the hook fired in, or null when
 * they cannot be read or are not Claude Code transcripts of this session. The hook gets
 * the main transcript's path even in a subagent, whose own transcript sits beside it;
 * a fork also holds the main one's history up to where it forked.
 */
function agentTranscripts(input, read) {
  const main = input.transcript_path;
  if (typeof main !== 'string' || main === '') return null;
  const agentId = input.agent_id;
  if (agentId !== undefined && (typeof agentId !== 'string' || !/^[\w-]+$/.test(agentId))) return null;
  const own = read(agentId === undefined ? main : `${main.replace(/\.jsonl$/, '')}/subagents/agent-${agentId}.jsonl`);
  if (own === null || !isSessionTranscript(own, input.session_id)) return null;
  const head = firstRecord(own);
  if (head?.type !== 'fork-context-ref') return [own];
  const parent = read(main);
  return parent === null ? [own] : [historyUpTo(parent, head.parentLastUuid), own];
}

/**
 * The hook's output for PreToolUse `input`, or null to print nothing.
 * `read(path)` returns a file's contents as a Buffer, or null when it cannot be read.
 */
function decide(input, read) {
  const command = typeof input.tool_input?.command === 'string' ? input.tool_input.command : '';
  const parts = commands(command);
  const textWrite = parts.some(writes);
  if (!textWrite && !parts.some(part => HINTED.some(pattern => pattern.test(part)))) return null;
  const transcripts = textWrite ? agentTranscripts(input, read) : null;
  if (transcripts !== null && !clearedSinceCompaction(transcripts)) {
    return {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: DENY_REASON,
      },
    };
  }
  return { hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext: HINT } };
}

function readFile(path) {
  try {
    return fs.readFileSync(path);
  } catch {
    return null;
  }
}

function main() {
  let input;
  try {
    input = JSON.parse(fs.readFileSync(0, 'utf8'));
  } catch {
    return;
  }
  if (!input || typeof input !== 'object' || Array.isArray(input)) return;
  const output = decide(input, readFile);
  if (output) process.stdout.write(`${JSON.stringify(output)}\n`);
}

if (require.main === module) {
  try {
    main();
  } catch {
    // Never block a write over a failure of this hook.
  }
}

module.exports = { DENY_REASON, HINT, decide };
