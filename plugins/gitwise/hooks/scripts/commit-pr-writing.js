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
 * most, so a transcript that lags the conversation costs a turn, never a lockout.
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
const MESSAGE_FLAG = /\s(?:-[a-zA-Z]*[mF]|--message\b|--file\b)/;
// Words that run the command after them: assignments such as `SKIP=x`, keywords, wrappers.
const PREFIX = /^(?:[A-Za-z_]\w*=(?:"[^"]*"|'[^']*'|\S*)|then|do|else|time|env|command|exec|!|\{)\s+/;
const SKILL_NAME = 'commit-pr-writing';
const SKILL_BODY_PREFIX = 'Base directory for this skill: ';
const SKILL_BODY = /^Base directory for this skill: .*[\\/]commit-pr-writing\s*$/m;

/**
 * The simple commands in shell `command`, split at control operators and stripped of
 * leading `PREFIX` words, so that a phrase inside an argument (`rg "git commit"`) is not
 * taken for a command. The split does not parse quotes: a line of a quoted message or
 * heredoc counts as a command of its own, and a command run as a string, as in
 * `bash -c "git commit -m x"`, is not seen.
 */
function commands(command) {
  return command.split(/[;&|\n(`]/).map(part => {
    let rest = part.trim();
    while (PREFIX.test(rest)) rest = rest.replace(PREFIX, '');
    return rest;
  });
}

/** Whether simple command `part` writes a commit message or a PR title or body. */
function writes(part) {
  if (HELP.test(part)) return false;
  if (COMMIT.test(part)) return !NO_EDIT.test(part) || MESSAGE_FLAG.test(part);
  if (PR_CREATE.test(part)) return true;
  return PR_EDIT.test(part) && PR_TEXT_FLAG.test(part);
}

/** Whether `command` writes a commit message or a PR title or body. */
function writesText(command) {
  return commands(command).some(writes);
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

function isOwnDeny(record) {
  const content = record.type === 'user' ? record.message?.content : null;
  if (!Array.isArray(content)) return false;
  return content.some(block => {
    if (block?.type !== 'tool_result' || block.is_error !== true) return false;
    return textBlocks(block.content).some(text => text.includes(DENY_MARKER));
  });
}

/**
 * Whether transcript JSONL `buf` shows a load of the skill or this hook's earlier deny.
 * Transcripts run to hundreds of megabytes, past the longest string Node can hold, so
 * the search stays on the Buffer and parses only the lines that name the skill.
 */
function cleared(buf) {
  for (let at = buf.indexOf(SKILL_NAME); at >= 0; ) {
    const start = buf.lastIndexOf(0x0a, at) + 1;
    const newline = buf.indexOf(0x0a, at);
    const end = newline < 0 ? buf.length : newline;
    const line = buf.toString('utf8', start, end);
    if (line.includes(SKILL_BODY_PREFIX) || line.includes(DENY_MARKER)) {
      try {
        const record = JSON.parse(line);
        if (record && typeof record === 'object' && (isSkillLoad(record) || isOwnDeny(record))) return true;
      } catch {
        // A partial last line: the transcript is written while the session runs.
      }
    }
    at = newline < 0 ? -1 : buf.indexOf(SKILL_NAME, newline);
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
  if (at < 0) return Buffer.alloc(0);
  const newline = buf.indexOf(0x0a, at);
  return newline < 0 ? buf : buf.subarray(0, newline);
}

/** The first record of JSONL `buf`, or null. */
function firstRecord(buf) {
  const newline = buf.indexOf(0x0a);
  try {
    return JSON.parse(buf.toString('utf8', 0, newline < 0 ? buf.length : newline));
  } catch {
    return null;
  }
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
  if (transcripts !== null && !transcripts.some(cleared)) {
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

module.exports = { DENY_REASON, HINT, decide, writesText };
