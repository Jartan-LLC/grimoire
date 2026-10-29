# sizecheck

Reports the gzipped size of each file in a build folder and fails when one is over budget.

- Node 20 or later, no dependencies.
- `npm test` runs the tests.
- The flags are a public interface: CI configs in other repositories pass them. Ask before
  changing what an existing flag does.
