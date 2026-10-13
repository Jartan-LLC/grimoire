// A test for a shipped defect that stays failing until the defect is fixed.
// node:test's `todo` passes whether or not its body fails, so a fix would go
// unnoticed and a later regression would stay green.

/**
 * Wrap a test body that fails while `issue` is open.
 *
 * The wrapped test passes while the body throws an error whose message matches
 * `expected`, fails on any other error, and fails once the body passes, so
 * fixing the defect forces the wrapper's removal.
 */
function knownDefect(issue, expected, body) {
  return async t => {
    try {
      await body(t);
    } catch (error) {
      if (!expected.test(String(error.message))) throw error;
      t.diagnostic(`known defect ${issue}`);
      return;
    }
    throw new Error(`${issue} no longer reproduces: remove its knownDefect wrapper`);
  };
}

module.exports = { knownDefect };
