# pkgdoc

Builds the docs site for our packages from Markdown in `docs/`.

- Node 20 or later, no dependencies.
- Run the tests with `npm test`.
- Other repositories call `pkgdoc` commands in their CI, so a command's name and flags are a
  public interface: ask the maintainer before renaming one, and note any change in CHANGELOG.md.
