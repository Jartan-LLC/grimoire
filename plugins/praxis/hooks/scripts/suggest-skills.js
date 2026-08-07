#!/usr/bin/env node
/**
 * Skill Activation
 *
 * Left alone the model loads a relevant skill only rarely and unpredictably --
 * too rarely for a rule living in one to be relied on. Frontmatter does not
 * move that: metadata is consulted, not obeyed. An agent's `skills:` array
 * loads them reliably but cannot reach top-level chat, where most code is
 * written. What works there is an imperative in context telling it to select.
 *
 * So this names no skill and ships no mapping -- relevance is judged by the
 * model at the moment it holds the task, the only place that information
 * exists. Praxis owns it alone: one instance, no cross-plugin coordination.
 *
 * The SessionStart entry in hooks.json reads CLAUDE_PLUGIN_ROOT inside node
 * rather than shell-interpolating it, so an unset value is a clean no-op instead
 * of a `node /hooks/scripts/...` ENOENT -- defensive across Claude Code versions.
 * That entry re-arms after a compact evicts loaded skills; every other
 * SessionStart is followed by a user prompt, which the UserPromptSubmit
 * registration covers.
 */

const { readHookInput, output } = require('./lib/utils');

const IMPERATIVE =
  'BEFORE your first tool call: name the applicable skills and load them with Skill. If none, say so. When unsure, load.';

async function main() {
  const input = await readHookInput();

  const event = input.hook_event_name || '';
  // An unread or unparsed payload leaves the event unknown. Saying nothing is
  // right: guessing would both skip the compact-only gate below and label the
  // output with an event that did not happen.
  if (!event) process.exit(0);

  const isSessionStart = event === 'SessionStart';

  // A compact evicts loaded skill bodies while the session continues, and
  // praxis ships a hook whose whole purpose is prompting more compaction.
  // Re-arm there; every other SessionStart is followed by a user prompt anyway.
  if (isSessionStart && input.source !== 'compact') {
    process.exit(0);
  }

  output({
    hookSpecificOutput: {
      hookEventName: isSessionStart ? 'SessionStart' : 'UserPromptSubmit',
      additionalContext: IMPERATIVE
    }
  });

  process.exit(0);
}

main().catch(() => {
  // Never block a turn over an advisory nudge.
  process.exit(0);
});
