# Changelog

## 1.1.3

- The skills adapted from wshobson/agents, everything-claude-code and claude-mpm-skills now ship their source's MIT notice as a `LICENSE-<project>` file in each skill's directory, and the README says which skill came from which project.

## 1.1.2

- `python-api-docs` no longer points to praxis skills, which may not be
  installed.
- `python-api-docs` says to put only your project's public modules on the API reference page.
- In `python-code-style`'s examples, `get_user`'s docstring no longer restates its signature, and `process_batch`'s no longer repeats the default its signature declares.
- The README templates in `python-code-style` and `python-packaging` are for a new README, where a project that has a CONTRIBUTING.md gets a pointer to it instead of development setup; your agent keeps an existing README's shape. `python-code-style` keeps an existing CHANGELOG.md's format and uses Keep a Changelog only for a new one.
- `python-project-structure` has your agent explain a component's organization in that component's own README, in a new project or one that keeps component READMEs, and state what each package owns in its `__init__.py` docstring.

## 1.1.1

- Three broken links to skills' reference files fixed, and Markdown formatting
  fixes across the README and skills.
