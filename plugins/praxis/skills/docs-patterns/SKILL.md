---
name: docs-patterns
description: Documentation conventions -- doc types, structure, tone, per-type rules, and quality standards.
when_to_use: Writing, editing, or reviewing documentation -- a README, CONTRIBUTING.md, a release procedure such as RELEASING.md, changelog entries and release notes, docs pages, or agent instruction files such as CLAUDE.md and AGENTS.md.
user-invocable: false
---

# Documentation Writing Patterns

Before writing, **load `praxis:plain-writing`** (what to keep and cut, plain voice, the final wording pass) and **read 2-3 existing docs in the same category** to match their tone and structure.

## Writing Style

Imperative for instructions ("Use X..."), declarative for specifications ("The User model has these fields..."). If a table communicates it better than prose, use a table.

## Doc Types

Pick the type before the shape -- the four Diataxis types each want a different shape. Two questions place any doc: **action** (doing) or **cognition** (understanding)? **Study** (learning) or **work** (the task at hand)?

| Type | Purpose | Shape | Which am I writing? |
|------|---------|-------|---------------------|
| Tutorial | Learning-oriented -- teach a newcomer by doing | Guided, sequential lesson whose steps are guaranteed to work | "Teaching a beginner start-to-finish; if they follow along they succeed." |
| How-to | Task-oriented -- reach one real goal with existing skills | Numbered steps for a single task; assumes competence | "Helping a competent user accomplish one specific goal." |
| Reference | Information-oriented -- authoritative facts consulted mid-task | Austere, structured to mirror the code, consistent patterns and tables | "Describing what *is* -- consulted, not read through." |
| Explanation | Understanding-oriented -- the why, context, trade-offs | Discursive prose; weighs alternatives and reasoning | "Explaining *why* -- read away from the code to understand." |

The **Section Structure** below is the **reference** shape. Don't force tutorials, how-tos, or explanations into it -- each has its own shape above.

## Files with their own rules

Before editing one of these, read its file in this skill's directory; a reviewer reads the matching file under `references/`.

| Document | Read |
|---|---|
| A changelog or release notes | `changelog.md` |
| A README, including a package page or a component's README | `readme.md` |
| CONTRIBUTING.md or other contributor docs | `contributing.md` |
| RELEASING.md or another release procedure | `releasing.md` |
| CLAUDE.md, AGENTS.md, the files they import or name as the rules, `.claude/rules/`, other tools' equivalents | `agent-files.md` |

## Section Structure

The **reference** shape (see Doc Types). Reference pages follow a consistent pattern:

1. **H1 title** with a one-line description
2. **Overview** -- brief intro, bullet list of capabilities/features
3. **Configuration** -- tables for settings/env vars (Setting | Default | Description)
4. **Usage** -- practical code examples showing realistic patterns
5. **Implementation details** -- topic-specific sections as needed
6. **See Also** -- related doc links

## Two Audiences

Write for whichever audience will actually read the doc:

| Trait | Use it (human, published) | Navigate / change it (contributor + AI agent) |
|-------|---------------------------|-----------------------------------------------|
| Register | Narrative, scannable prose | Terse; structure over narrative |
| Sections | Context carried across the page | Self-contained, retrievable in isolation |
| Headings | Guide the eye | Stable and predictable; no skipped levels |
| References | "As shown above" is fine | Explicit -- name the thing, not "the method above" |
| Facts | May live inside prose | Stated plainly, one name per concept, not buried |

Both trace to one source: **docstrings + type annotations**. The "use it" doc narrates from them; the "navigate/change it" doc indexes them. State a fact once at its source -- types already carry the shapes, so prose shouldn't restate them -- and reference it from both.

## Strictness Bars

"Examples work" and "links resolve" only hold if a check enforces them. Each bar is a CI gate, stated tool-free:

| Bar | What it catches |
|-----|-----------------|
| Strict build (warnings -> errors) | Malformed directives, missing or dead references shipped as silent warnings |
| Internal link check | Dead cross-references to moved or deleted docs |
| External link check | Link rot -- dead outbound URLs |
| Tested / executed snippets | Stale examples that no longer run or match the code |
| Nav / table-of-contents completeness | Orphan and unlisted pages nothing links to |
| Cross-reference check | Broken reference-style pointers to renamed or removed targets |

Language toolchain implementing these bars (plus API docs generated from docstrings): see `pythonica:python-api-docs`.

## Conventions

- **Tables** for reference content (settings, fields, endpoints). 3-4 columns max.
- **Code examples** in Usage sections -- complete enough to copy-paste, with error handling where relevant.
- **Internal links** use relative markdown: `[Doc Name](FILENAME.md)`
- **Code examples must work** -- enforce with the tested-snippets bar (see Strictness Bars), not manual review alone.

## Change narration

Prose that narrates the change which produced the page, or inventories where else its fact applies, is addressed to whoever reviews the diff rather than whoever is following the page. It arrives looking like context and costs the reader a sentence answering a question they did not ask.

**Test:** would a reader who never saw the change, wanting only what this section is for, do anything differently for having read it? No -> cut.

`Or from source. This project installs with uv rather than pip -- in CI, in the devcontainer and in the Docker image:` -- the reader is installing locally. Which installer the project stopped using, and the three other places the new one is also used, change nothing they type. `Or from source, with uv:` is the whole of it.

Change narration's code-comment form is what `comment-hygiene`'s *Density* calls PR narration, and one migration commonly produces both, so a diff carrying it in comments is worth reading for it in the docs too. Rationale that needs a home goes in the commit message (under a merge setting that drops it, where `gitwise:commit-pr-writing` says), or in a decision record the project keeps.

## What to Avoid

- Verbose explanations where a table or code block would be clearer
- Anything `plain-writing`'s Cut list names
- Documentation that doesn't match the actual code
