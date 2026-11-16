#!/usr/bin/env node
/**
 * Skill Activation When the Work Changes Kind
 *
 * suggest-skills.js asks the main thread to load its skills at each user prompt
 * and a subagent after its brief. A turn that starts on one kind of work and
 * moves on to another, such as from a plan to the code, is not asked again, so
 * the skills for the later work go unloaded.
 *
 * So after each file tool call this keeps, per agent, the types of file the
 * agent has touched, and on its first file of each new type asks it to load
 * the skills that apply. Like suggest-skills.js it names no skill and ships no
 * mapping from types to skills: the model judges relevance.
 *
 * It ignores which skills the agent has loaded: it cannot tell a load made
 * for the next file from one that answers the last reminder, so letting a load
 * excuse a type would either hide the reminder a turn from docs to code needs
 * or, kept to loads made unprompted, almost never apply.
 *
 * A compact evicts the skills an agent loaded, so hooks.json also runs this on
 * the SessionStart that follows one, which empties the agent's state: each type
 * it reaches after that reminds again. That entry loads this file through
 * `require`, as the one for suggest-skills.js does, and calls `cli`.
 *
 * Each agent has its own state file, so parallel subagents never write the
 * same one. The file is replaced by a rename, so a reader never sees it half
 * written. Parallel calls within one agent may still lose each other's update:
 * a type then reminds a second time.
 */

const fs = require('fs');
const path = require('path');
const { readHookInput, readFile, writeFile, log, output } = require('./lib/utils');
const { sessionId: toSessionId, stateFilePath, sweepStaleState } = require('./lib/session-state');
const { fileTypeImperative } = require('./lib/skill-context');

const STATE_FILE_PREFIX = 'claude-skill-file-types-';
const MAIN_THREAD = 'main';
const EMPTY_STATE = Object.freeze({ types: [] });

// A repository chooses its file names, and the reminder reaches the agent as
// harness context: only a short plain token is ever named in it.
const PLAIN_EXTENSION = /^[a-z0-9]{1,10}$/;
const UNNAMED_TYPE = 'unnamed';

/**
 * The type of the file at `filePath`: a dot and the lower-cased text after its
 * name's last dot when that is a short plain token, such as `.py` or
 * `.gitignore`, and otherwise UNNAMED_TYPE, which every such file shares.
 */
function fileType(filePath) {
  const name = path.basename(filePath);
  const dot = name.lastIndexOf('.');
  const extension = dot === -1 ? '' : name.slice(dot + 1).toLowerCase();
  return PLAIN_EXTENSION.test(extension) ? `.${extension}` : UNNAMED_TYPE;
}

/** The path a file tool call names: `file_path` for Read, Edit and Write, `notebook_path` for NotebookEdit. */
function touchedPath(toolInput) {
  if (!toolInput || typeof toolInput !== 'object') return null;
  const file = toolInput.file_path ?? toolInput.notebook_path;
  return typeof file === 'string' && file !== '' ? file : null;
}

/**
 * The agent's state after hook `input`, and the file type to remind it of, or null.
 * `state` is `{ types }`, the types the agent has touched; a SessionStart after
 * a compact empties it. Returns the same `state` object when nothing changed,
 * which `run` relies on to skip the write.
 */
function step(state, input) {
  if (input.hook_event_name === 'SessionStart') {
    return { state: input.source === 'compact' ? EMPTY_STATE : state, remind: null };
  }
  const file = touchedPath(input.tool_input);
  if (file === null) return { state, remind: null };
  const type = fileType(file);
  if (state.types.includes(type)) return { state, remind: null };
  return { state: { types: [...state.types, type] }, remind: type };
}

/** The agent's state file's contents, or null when it has none; a corrupt file reads as empty. */
function readState(file) {
  const text = readFile(file);
  if (text === null) return null;
  try {
    const parsed = JSON.parse(text);
    return { types: Array.isArray(parsed.types) ? parsed.types.filter(type => typeof type === 'string') : [] };
  } catch {
    return EMPTY_STATE;
  }
}

/** Replace `file` with `text` through a temp file in its directory, so a concurrent reader sees the old text or the new. */
function writeAtomically(file, text) {
  const temp = `${file}.${process.pid}.tmp`;
  writeFile(temp, text);
  try {
    fs.renameSync(temp, file);
  } catch (err) {
    fs.rmSync(temp, { force: true });
    throw err;
  }
}

/** The state file of the agent hook `input` fired in, or null when its `agent_id` is unusable. */
function agentStateFile(input) {
  // Only a subagent's hook input carries agent_id.
  const agentId = input.agent_id ?? MAIN_THREAD;
  if (typeof agentId !== 'string' || !/^[\w-]+$/.test(agentId)) return null;
  return stateFilePath(STATE_FILE_PREFIX, `${toSessionId(input.session_id)}-${agentId}`);
}

/** The reminder for hook `input`, or null, updating the agent's state file on the way. */
function run(input) {
  const file = agentStateFile(input);
  if (file === null) return null;
  let state = readState(file);
  if (state === null) {
    // A sweep reads the whole temp directory, and this hook runs on every Read: sweep once per agent.
    sweepStaleState([STATE_FILE_PREFIX], [file]);
    state = EMPTY_STATE;
  }
  const next = step(state, input);
  if (next.state !== state) writeAtomically(file, JSON.stringify(next.state));
  if (next.remind === null) return null;
  return fileTypeImperative(next.remind === UNNAMED_TYPE ? null : next.remind);
}

async function main() {
  const input = await readHookInput();
  if (Array.isArray(input)) return;
  const reminder = run(input);
  if (reminder !== null) {
    output({ hookSpecificOutput: { hookEventName: 'PostToolUse', additionalContext: reminder } });
  }
}

/** Run the hook on its stdin and exit 0, whatever happens. */
function cli() {
  main()
    .catch(err => log(`[Hook] suggest-skills-per-file-type error: ${err.message}`))
    .finally(() => process.exit(0));
}

module.exports = { agentStateFile, cli, fileType, run, step, UNNAMED_TYPE, writeAtomically };

if (require.main === module) cli();
