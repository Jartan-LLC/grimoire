#!/bin/bash
#
# postAttachCommand -- runs each time a client attaches to the container.
# Refreshes Claude Code marketplaces AND installed plugins so the newest
# versions are picked up on the next session. Best-effort: every step swallows
# errors so a network hiccup never blocks attaching.

if command -v claude &>/dev/null; then
    # Refresh marketplace metadata first so plugin updates resolve to the latest
    # available versions.
    claude plugins marketplace update 2>/dev/null || true

    # `claude plugins update` acts on one plugin at a time and has no bulk form,
    # so enumerate installed plugins (id + scope) and update each within its own
    # scope. node ships with the claude CLI, so use it to parse the JSON listing.
    # Each update acts on a single record per (id, scope) -- this project's if it
    # has one, otherwise the first found -- so ids listed for several projects
    # resolve to the same record more than once. Harmless, and cheaper than
    # de-duplicating.
    if command -v node &>/dev/null; then
        claude plugins list --json 2>/dev/null | node -e '
let input = "";
process.stdin.on("data", (d) => (input += d));
process.stdin.on("end", () => {
  let plugins = [];
  try { plugins = JSON.parse(input); } catch (e) {}
  if (!Array.isArray(plugins)) plugins = [];
  for (const p of plugins) {
    if (p && p.id) console.log(p.id, p.scope || "user");
  }
});
' | while read -r plugin_id scope; do
            [ -n "$plugin_id" ] || continue
            claude plugins update "$plugin_id" --scope "$scope" 2>/dev/null || true
        done
    fi
fi
