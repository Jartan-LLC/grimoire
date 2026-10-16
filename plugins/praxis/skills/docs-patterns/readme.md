# README Files

The project's own rules win where they speak (CONTRIBUTING.md and the docs it links), over the lines below and over a generated file's existing shape: put what they ask for in the README, where the file says added notes go. Unless the task is the README itself, apply these lines only to what your change adds or makes false; put new items where the project keeps that kind.

- Search every README for each command, option, setting, default, requirement, component or capability your change adds, removes, renames or alters, and fix each list, table, example and claim it makes false. List stale translations in the PR description, if any exist. If what the project or a component gives changed, rewrite its opening line and every copy (manifest description, root table row).
- Steps, examples and status must hold for the code the install steps run today; mark anything newer with its version, else "unreleased", unless the README says it describes the default branch. Add no URL, version or fact that the change, the tree or the release record does not show.
- Restate nothing another file or the program's help holds, beyond a short summary or example and a link saying what it holds. Where pages for users exist, the full reference (every setting, option, tool) goes there.
- If the README is also a package page (pyproject.toml's `readme`, an npm package), use absolute URLs for links and images unless the build rewrites them, and word any status mark so it stays true once the next release publishes the page.
