---
name: python-api-docs
description: Render Python docstrings into a browsable, published API reference with Sphinx, autodoc, napoleon, and MyST.
when_to_use: Setting up an API reference site, wiring Sphinx + autodoc + napoleon, running docstring examples under doctest, or adding a strict docs build as a CI gate.
---

# Python API Documentation

`pythonica:python-code-style` teaches you to *write* google-style docstrings; this skill *renders* them into a published API reference. The toolchain is Sphinx + `autodoc` + `napoleon` + MyST, gated strictly in CI so the reference can't silently rot. For the general documentation rules (tone, brevity, structure) this toolchain serves, see `praxis:docs-patterns`.

## Core Concepts

### 1. Docstrings are the single source

Autodoc imports your package and extracts docstrings at build time. The reference is generated, never hand-copied -- so it can't drift from the code.

### 2. Annotations render themselves -- don't duplicate types

With type hints present, autodoc renders them into the signature (`autodoc_typehints` defaults to `"signature"`). Restating `(str)` in an `Args` line duplicates the annotation and drifts when the type changes. Keep `Args` descriptions prose-only.

### 3. Examples that run can't rot

The `>>> Example` blocks `python-code-style` recommends are executable. Run them under `sphinx.ext.doctest` and a broken example fails the build instead of misleading a reader.

### 4. A strict build is a CI gate

`sphinx-build -W` turns every warning (a missing module, an unresolved `:func:`, a bad cross-reference) into an error. Wire it into CI and the docs stay correct on every PR.

## Quick Start

Declare the toolchain as an optional-dependency extra, then build:

```toml
# pyproject.toml
[project.optional-dependencies]
docs = [
    "sphinx>=9,<10",     # site generator (reads google docstrings via napoleon)
    "myst-parser>=5,<6", # author pages in Markdown, not reStructuredText
    "furo>=2025.12",     # theme (CalVer -- date floor, no semver major to cap)
]
```

```bash
pip install -e '.[docs]'
sphinx-build -W -b html    docs docs/_build/html      # strict HTML build
sphinx-build -W -b doctest docs docs/_build/doctest    # run every >>> example
```

## Fundamental Patterns

### Pattern 1: Wire Sphinx + MyST + napoleon (`conf.py`)

One `conf.py` enables the whole toolchain. Each extension owns one job:

| Extension | Job |
| --- | --- |
| `sphinx.ext.autodoc` | Import the package, pull docstrings from source |
| `sphinx.ext.napoleon` | Parse google-style `Args:` / `Returns:` / `Raises:` |
| `sphinx.ext.autosummary` | Generate per-submodule stub pages recursively |
| `sphinx.ext.doctest` | Execute `>>>` examples under `-b doctest` |
| `sphinx.ext.intersphinx` | Resolve cross-references into other projects' docs |
| `sphinx.ext.viewcode` | Link each object to highlighted source |
| `myst_parser` | Author narrative pages in Markdown |

```python
# docs/conf.py
import sys
from pathlib import Path

# Make the src-layout package importable for autodoc (works without an install too).
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

project = "My Project"
author = "Your Name"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "myst_parser",
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False

autodoc_typehints = "signature"  # default: types go in the signature, not the description
autosummary_generate = True      # default since Sphinx 4.0: emit stub pages

myst_enable_extensions = ["colon_fence", "deflist"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

exclude_patterns = ["_build"]
html_theme = "furo"
```

**MkDocs alternative -- flagged.** `mkdocstrings` (with Material for MkDocs) is the MkDocs-native equivalent, but the MkDocs ecosystem is mid-transition. MkDocs 2.0 (announced Jan 2026) drops plugin support entirely, which breaks `mkdocstrings` and Material; Material has entered maintenance mode, and its successor **Zensical** is still `v0.0.x` with API-reference feature-parity in progress. **Prefer Sphinx today**; revisit Zensical once it reaches parity and stabilizes.

### Pattern 2: Don't duplicate types

Annotations render into the signature, so `Args` lines describe *meaning*, not type:

```python
def get_user(user_id: str, *, include_deleted: bool = False) -> User:
    """Fetch a user by primary key.

    Args:
        user_id: Primary key of the user.          # prose only -- NOT "(str) Primary key..."
        include_deleted: Also return soft-deleted rows.

    Returns:
        The matching user.

    Raises:
        UserNotFoundError: If no user has that ID.
    """
```

Autodoc renders `user_id (str)` from the annotation itself. See `pythonica:python-code-style` Pattern 5 for the docstring shape this builds on.

### Pattern 3: Build the reference page -- avoid the thin-`__init__` trap

A bare `.. automodule:: mypkg` on a re-export-only `__init__.py` renders **only the package docstring** -- none of the submodules it re-exports. Two ways out.

**Per-module `automodule`** (explicit; MyST `eval-rst` fence). Stale module names break the strict build, forcing the page to track the code:

````markdown
# API reference

```{eval-rst}
.. automodule:: mypkg.client
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: mypkg.errors
   :members:
   :undoc-members:
   :show-inheritance:
```
````

**Autosummary `:recursive:`** (automatic; scales to large packages). Walks the package and generates a stub page per submodule; needs a recursive `_templates/autosummary/module.rst` that loops over submodules:

````markdown
```{eval-rst}
.. autosummary::
   :toctree: _generated
   :recursive:

   mypkg
```
````

Use per-module for a handful of modules; switch to autosummary `:recursive:` when hand-listing them becomes the maintenance burden.

## Advanced Patterns

### Pattern 4: Cross-references + intersphinx

Cross-reference roles link objects and fail the strict build when a target is wrong. In docstrings and `eval-rst` (reStructuredText), use `:func:` / `:class:` / `:mod:`; in MyST Markdown pages, use `{py:func}` / `{py:class}`:

```python
def connect(dsn: str) -> Connection:
    """Open a connection.

    Prefer :func:`mypkg.client.connect_pool` for concurrent callers.
    Returns a :class:`mypkg.client.Connection` wrapping :class:`socket.socket`.
    """
```

```markdown
See {py:func}`mypkg.client.connect` and the stdlib {py:class}`pathlib.Path`.
```

With `intersphinx_mapping` set (Pattern 1), unresolved references like `socket.socket` or `pathlib.Path` fall back to the mapped projects' inventories (`objects.inv`) and become live links -- no hardcoded URLs.

### Pattern 5: Run examples under doctest

`sphinx.ext.doctest` tests the `>>>` blocks in autodoc-included docstrings *and* narrative pages, with no special markup. Share common imports via `doctest_global_setup`:

```python
# docs/conf.py
doctest_global_setup = "import mypkg"
```

```python
def slugify(text: str) -> str:
    """Convert text to a URL slug.

    Example:
        >>> slugify("Hello World")
        'hello-world'
    """
```

```bash
sphinx-build -b doctest docs docs/_build/doctest   # 'hello-world' must match, or the build fails
```

Sphinx's doctest defaults include `ELLIPSIS`, so `...` already matches unstable output like `<object at 0x...>` -- no per-example `# doctest: +ELLIPSIS` directive needed (add a directive only to override a flag for one block).

### Pattern 6: Gate the docs build in CI

Run both builders under `-W` so warnings and failed examples block the merge:

```yaml
# .github/workflows/ci.yml
docs:
  runs-on: ubuntu-24.04
  steps:
    - uses: actions/checkout@v7
    - uses: actions/setup-python@v6
      with:
        python-version: "3.12"
    - run: pip install -e '.[docs]'          # runtime deps must import for autodoc
    - run: sphinx-build -W -b html    docs docs/_build/html      # warnings -> errors
    - run: sphinx-build -W -b doctest docs docs/_build/doctest    # examples must pass
```

Add `docs` to the aggregate check job's `needs`, and audit `.[docs]` for CVEs alongside `.[dev]`.

## Best Practices Summary

1. **Docstrings are the source** -- generate the reference with autodoc; never hand-copy signatures.
2. **Napoleon + google** -- set `napoleon_google_docstring = True`; author pages in MyST Markdown.
3. **Never restate types** -- annotations render into the signature; keep `Args` prose-only.
4. **Executable examples** -- run `>>>` blocks under `sphinx.ext.doctest` (`-b doctest`) so they can't rot.
5. **Cross-reference, don't hardcode** -- use `:func:`/`:class:` roles and `intersphinx_mapping` for external links.
6. **Escape the thin-`__init__` trap** -- per-module `automodule` or autosummary `:recursive:`, never a bare package `automodule`.
7. **Strict build in CI** -- `sphinx-build -W` for HTML and doctest; wire it into the check gate.
8. **Prefer Sphinx today** -- the MkDocs/mkdocstrings/Zensical stack is mid-transition; revisit when it stabilizes.

## See Also

- `pythonica:python-code-style` -- writing the google-style docstrings and type hints this renders.
- `praxis:docs-patterns` -- the general documentation style, structure, and strictness rules this toolchain serves.
