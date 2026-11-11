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
 * The text per event lives in lib/skill-context.js; subagents, which never see
 * UserPromptSubmit, get theirs through SubagentStart.
 *
 * The SessionStart entry in hooks.json reads CLAUDE_PLUGIN_ROOT inside node
 * rather than shell-interpolating it, so an unset value is a clean no-op instead
 * of a `node /hooks/scripts/...` ENOENT -- defensive across Claude Code versions.
 * That entry re-arms skill activation after a compact (lib/skill-context.js
 * says why).
 */

const { readHookInput, output } = require('./lib/utils');
const { contextFor } = require('./lib/skill-context');

async function main() {
  const context = contextFor(await readHookInput());
  if (context) output(context);
  process.exit(0);
}

main().catch(() => {
  // Never block a turn over an advisory nudge.
  process.exit(0);
});
