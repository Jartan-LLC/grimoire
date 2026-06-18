---
name: recursive-quality
description: Quality patterns, anti-patterns, and contract richness guidelines for recursive development.
---

# Recursive Quality

## Contract Richness

Wave 0 contracts set the ceiling. Thin contracts → thin implementations.

### Completeness
- Enumerate all operations, not just common ones
- Enums for closed sets (prevents string-typing drift)
- Error types alongside success types (`Record | ParseError`)
- Custom exception hierarchy — base + subtypes per failure domain

### Flexibility
- Batch interfaces (`list[Spec]`) over single-item
- Injectable I/O (write callables, output streams) for testability
- Union return types for expected failures; exceptions for unexpected

### Modularity
- Protocols/interfaces for DI — not concrete dependencies
- Factories/registries for runtime selection
- Structured return types (`RunResult`) over bare values

### Typing boundaries
- Untyped/dynamic values (`Any`, `object`) are acceptable at **input boundaries** — parsed records, CLI args, external data where the shape is genuinely unknown
- All **internal result types** (aggregation results, pipeline outputs, structured returns) must be fully typed — the shape is known at design time
- Contracts file contains: protocols, dataclasses, enums, type aliases, constants. No callable stubs.

## Critical Rules

These are never judgment calls. Implementers must not produce code that violates them. Reviewers must flag violations as Critical.

- **Typed returns.** No untyped/dynamic returns (`Any`, `object`, `interface{}`) on public functions or protocol methods. Use the specific type or union.
- **Structured returns.** No unstructured collection returns where contracts define or should define a structured type.
- **No absolute paths.** No hardcoded absolute paths in source or tests. Use the language's path library with relative paths.
- **Logging, not stderr.** Library code uses the language's logging framework with named loggers. Never write directly to stderr. Entry points configure level/format.
- **Typed protocol signatures.** Protocol/interface method parameters and returns must be fully typed. Untyped signatures cascade to every downstream module.

## Quality Patterns

- **Graceful degradation** — yield errors for bad input and continue. Don't crash the pipeline.
- **System boundary validation** — validate external input at the boundary. Don't trust parsed data.
- **Logging** — use the language's framework (`logging`, `pino`, `log`). Library code uses named loggers, never writes stderr. Entry points configure level/format.
- **Error handling** — union types for expected failures, exceptions for unexpected. Messages include field name, bad value, what was expected.
- **Exception hierarchy** — base project exception + specific subtypes. Part of Wave 0 contracts.
- **Cross-platform correctness** — use the language's path library (`pathlib`, `path.join`, `std::path`) for all file operations. Specify encoding explicitly on file I/O (e.g. `encoding="utf-8"`). No string path concatenation. No hardcoded absolute paths. No platform-specific assumptions.
- **Runtime versioning** — expose version programmatically. CLI supports `--version`.
- **Test coverage** — configure with minimum threshold. Coverage config in project config file.
- **Content-based detection** — auto-detect formats from content, not just file extensions.

## Anti-Patterns

- **God orchestrator** — orchestrator micromanaging every file. It manages waves and contracts, not implementation.
- **Shared file optimism** — assuming parallel agents won't conflict. Verify scope overlap before dispatching.
- **Context dumping** — passing full plan to every child. Each gets contract + scope only.
- **Test-after at depth** — skipping TDD at leaf level. Every level writes tests first.
- **Unbounded retry** — cap at 2, then escalate.
- **Artificial splitting** — files created just to delegate. Split for distinct algorithms only.
- **Over-specified plans** — prescribing file structure, test cases, sub-components. Agents discover through TDD.
- **Hardcoded absolute paths** — use relative paths from `__file__` or project root.
