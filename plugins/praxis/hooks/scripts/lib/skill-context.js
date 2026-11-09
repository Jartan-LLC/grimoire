/**
 * The skill-activation imperative suggest-skills.js injects, per hook event.
 *
 * Kept out of suggest-skills.js because hooks.json's SessionStart entry runs
 * that script through `require`: the script cannot check `require.main` before
 * reading stdin, so a test that loaded it would read stdin and exit the test
 * process.
 */

const IMPERATIVE =
  'BEFORE your first tool call: name the applicable skills and load them with Skill. If none, say so. When unsure, load.';

// A subagent gets this ahead of its brief. A skill on dividing work stays with
// the briefs that name one: a part that loads such a skill on its own splits
// again past the depth its parent planned.
const SUBAGENT_IMPERATIVE =
  'BEFORE your first tool call: name the skills that apply to the work your task asks for ' +
  '(its language, libraries and kind of work) besides any your task names, and load with Skill ' +
  'those not already in your context. Load a skill on dividing or delegating work only if your ' +
  'task names it. If none apply, say so. When unsure, load.';

const TEXT_BY_EVENT = new Map([
  ['SessionStart', IMPERATIVE],
  ['UserPromptSubmit', IMPERATIVE],
  ['SubagentStart', SUBAGENT_IMPERATIVE],
]);

/**
 * The hook output for a hook's stdin `input`, or null when it should print nothing.
 *
 * An event this hook does not serve, or an unread payload, gets nothing:
 * guessing would label the output with an event that did not happen.
 */
function contextFor(input) {
  const event = input && input.hook_event_name;

  // A compact evicts loaded skill bodies while the session continues, and
  // praxis ships a hook whose whole purpose is prompting more compaction.
  // Re-arm there; every other SessionStart is followed by a user prompt anyway.
  if (event === 'SessionStart' && input.source !== 'compact') return null;

  const text = TEXT_BY_EVENT.get(event);
  if (text === undefined) return null;
  return { hookSpecificOutput: { hookEventName: event, additionalContext: text } };
}

module.exports = { contextFor, IMPERATIVE, SUBAGENT_IMPERATIVE };
