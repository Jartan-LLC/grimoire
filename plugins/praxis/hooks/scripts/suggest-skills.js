#!/usr/bin/env node
/**
 * Skill Activation
 *
 * Left alone the model does sometimes load a relevant skill, but rarely and
 * unpredictably -- too rarely for a rule that lives in one to be relied on.
 * Strengthening a skill's own frontmatter does not move that: metadata is
 * consulted, not obeyed. An agent's `skills:` array loads them reliably but
 * cannot reach top-level chat, where most code is written. What works there is
 * an imperative in context telling the model to select.
 *
 * So this names no skill and ships no mapping. Relevance is judged by the model
 * at the moment it holds the task -- the only place that information exists --
 * and a static mapping would over-fire where the model picks the one relevant
 * skill out of a plugin's many.
 *
 * Praxis owns this alone: one instance, no dedup, no cross-plugin coordination.
 * Skills wanting higher activation frequency say so in their own frontmatter
 * rather than being listed here.
 */

const { readStdinJson, output } = require('./lib/utils');

const IMPERATIVE =
  'Before responding, identify which of your available skills are relevant to this task and load them first.';

async function main() {
  let input = {};
  try {
    input = await readStdinJson({ timeoutMs: 1000 });
  } catch {
    input = {};
  }

  const event = (input && input.hook_event_name) || '';

  // A compact evicts loaded skill bodies while the session continues, and
  // praxis ships a hook whose whole purpose is prompting more compaction.
  // Re-arm there; every other SessionStart is followed by a user prompt anyway.
  if (event === 'SessionStart' && input.source !== 'compact') {
    process.exit(0);
  }

  output({
    hookSpecificOutput: {
      hookEventName: event === 'SessionStart' ? 'SessionStart' : 'UserPromptSubmit',
      additionalContext: IMPERATIVE
    }
  });

  process.exit(0);
}

main().catch(() => {
  // Never block a turn over an advisory nudge.
  process.exit(0);
});
