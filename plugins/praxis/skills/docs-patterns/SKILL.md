---
name: docs-patterns
description: Documentation writing conventions — style, structure, tone, and quality standards.
when_to_use: Writing, editing, or reviewing documentation files.
---

# Documentation Writing Patterns

Before writing, **read 2-3 existing docs in the same category** to match their tone and structure.

## Writing Style

**Tone:** Technical but accessible. Imperative for instructions ("Use X..."), declarative for specifications ("The User model has these fields..."). No marketing language.

**Brevity is paramount.** A doc that could be 100 lines should not be 300. Every paragraph must earn its place. If a table communicates it better than prose, use a table. If a link to another doc covers it, don't restate it. Be precise, not exhaustive.

## Doc Types

Pick the type before the shape — the four Diátaxis types each want a different shape. Two questions place any doc: **action** (doing) or **cognition** (understanding)? **Study** (learning) or **work** (the task at hand)?

| Type | Purpose | Shape | Which am I writing? |
|------|---------|-------|---------------------|
| Tutorial | Learning-oriented — teach a newcomer by doing | Guided, sequential lesson whose steps are guaranteed to work | "Teaching a beginner start-to-finish; if they follow along they succeed." |
| How-to | Task-oriented — reach one real goal with existing skills | Numbered steps for a single task; assumes competence | "Helping a competent user accomplish one specific goal." |
| Reference | Information-oriented — authoritative facts consulted mid-task | Austere, structured to mirror the code, consistent patterns and tables | "Describing what *is* — consulted, not read through." |
| Explanation | Understanding-oriented — the why, context, trade-offs | Discursive prose; weighs alternatives and reasoning | "Explaining *why* — read away from the code to understand." |

The **Section Structure** below is the **reference** shape. Don't force tutorials, how-tos, or explanations into it — each has its own shape above.

## Section Structure

The **reference** shape (see Doc Types). All reference- and README-style docs follow a consistent pattern:

1. **H1 title** with a one-line description
2. **Overview** — brief intro, bullet list of capabilities/features
3. **Configuration** — tables for settings/env vars (Setting | Default | Description)
4. **Usage** — practical code examples showing realistic patterns
5. **Implementation details** — topic-specific sections as needed
6. **See Also** — related doc links

## Two Audiences

Write for whichever audience will actually read the doc:

| Trait | Use it (human, published) | Navigate / change it (contributor + AI agent) |
|-------|---------------------------|-----------------------------------------------|
| Register | Narrative, scannable prose | Terse; structure over narrative |
| Sections | Context carried across the page | Self-contained, retrievable in isolation |
| Headings | Guide the eye | Stable and predictable; no skipped levels |
| References | "As shown above" is fine | Explicit — name the thing, not "the method above" |
| Facts | May live inside prose | Stated plainly, one name per concept, not buried |

Both trace to one source: **docstrings + type annotations**. The "use it" doc narrates from them; the "navigate/change it" doc indexes them. State a fact once at its source — types already carry the shapes, so prose shouldn't restate them — and reference it from both.

## Strictness Bars

"Examples work" and "links resolve" only hold if a check enforces them. Each bar is a CI gate, stated tool-free:

| Bar | What it catches |
|-----|-----------------|
| Strict build (warnings → errors) | Malformed directives, missing or dead references shipped as silent warnings |
| Internal link check | Dead cross-references to moved or deleted docs |
| External link check | Link rot — dead outbound URLs |
| Tested / executed snippets | Stale examples that no longer run or match the code |
| Nav / table-of-contents completeness | Orphan and unlisted pages nothing links to |
| Cross-reference check | Broken reference-style pointers to renamed or removed targets |

Language toolchain implementing these bars (plus API docs generated from docstrings): see `pythonica:python-api-docs`.

## Conventions

- **Tables** for reference content (settings, fields, endpoints). 3-4 columns max.
- **Code examples** in Usage sections — complete enough to copy-paste, with error handling where relevant.
- **Internal links** use relative markdown: `[Doc Name](FILENAME.md)`
- **No redundancy** — don't repeat information documented elsewhere. Link instead.
- **Code examples must work** — enforce with the tested-snippets bar (see Strictness Bars), not manual review alone.

## What to Avoid

- Verbose explanations where a table or code block would be clearer
- Repeating content from other docs (link to it)
- Obvious statements that don't add value
- Multiple ways of saying the same thing
- Documentation that doesn't match the actual code
