// A test for a shipped defect that stays failing until the defect is fixed.
// node:test's `todo` passes whether or not its body fails, so a fix would go
// unnoticed and a later regression would stay green.

/**
 * Wrap a test body that fails while `issue` is open.
 *
 * The wrapped test passes while the body throws, and fails once the body
 * passes, so fixing the defect forces the wrapper's removal.
 */
function knownDefect(issue, body) {
  return async t => {
    try {
      await body(t);
    } catch (error) {
      t.diagnostic(`known defect ${issue}: ${String(error.message).split('\n')[0]}`);
      return;
    }
    throw new Error(`${issue} no longer reproduces: remove its knownDefect wrapper`);
  };
}

module.exports = { knownDefect };
