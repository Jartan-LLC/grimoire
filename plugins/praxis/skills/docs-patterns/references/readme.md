# Reviewing README changes

Where the project's own rules, checks or tools decide a point (agent instruction files,
CONTRIBUTING.md and the docs it links, generator config, packaging metadata, a lint step), raise
nothing against them. Review against the README lines in the docs-patterns skill (`../readme.md`)
first, including their scope, then these checks. A wrong migration, upgrade, recovery or removal
step is Critical.

## What not to raise

- A README in a working directory (`tests/`, `scripts/`) is for whoever works there. Check only
  what the change made false in it; never ask to move it into CONTRIBUTING.md.
- READMEs in vendored or third-party trees belong to their upstream.
- A dated "What's new" section inside a README is a change record: judge it as changelog text.
- Translations (`README.<lang>.md`, or a directory such as `readme_i18n/`) left stale, unless the
  project keeps them in step with the source; then check them as the source. Where none exist, a
  translation claim in the PR description ("No translations to update.") is itself a finding.
- A missing README (beyond the one question to the user that `information-placement` allows), or a
  missing promise of what users may rely on across updates: the project's call.

## Project rules the README must still meet

Where CONTRIBUTING.md asks each README for something ("Include usage instructions"), a generated
layout, or the writer file's "Restate nothing another file or the program's help holds", does not
excuse leaving it out. A component README that is only its generated options table fails readers
asking how to run it. Verify: read CONTRIBUTING.md, then the README.

## Stale claims

**Promises, not just names.** For each capability the change removes or alters, read every
sentence that could still promise it; searching for its name misses promises. Verify:
list what the diff removes, then read the opening, feature list and comparison tables.

- Bad: after a change that stops promising a knowledge graph, the README still says "mem0 on
  pgvector for semantic search and a knowledge graph". Better: "mem0 on pgvector for semantic
  search."

**Limits carried from the change.** When the change adds or alters an option or path, its README
text keeps each limit stated in the PR description or the help text that decides which value or
path a user picks, and claims nothing beyond it; else users pick a value that does not do what
they expect. Verify: read the PR description and the option's `--help` text, then the new text.

- Bad: a `--sanitize=auto|always|never` paragraph that never says `auto` keeps the plain-text
  exception of `--strip-ansi=auto`.

**Status for what the install steps run.** Find what the install steps run (newest tag or
release, `pip index versions <pkg>`, `npm view <pkg> version`, the image tag the compose file
pulls) and check that each new step or example holds for it or is marked; else users of the
released code hit a step that fails. On a package page, "(unreleased)" goes false once the next
release publishes the page; prefer "releases up to 0.65.5 also run on Python 3.10".

**Unsourced additions.** A URL or version written from memory can be dead or wrong. Verify: grep
the diff for added `http` links and version numbers; one found in neither the change, the tree nor
the release record is unsourced.

## Generated and shared text

**Generated text.** Where the project's contributor docs say how its READMEs are written, they
decide; a footer alone does not make `NOTES.md` the place. Otherwise text inside generator markers
(`<!-- BEGIN_TF_DOCS -->`) or under a "This file was auto-generated" note changes through its
source (a manifest, a module's `.tf` variable and output descriptions, `NOTES.md`, a template),
and the block matches what the generator emits from that source; else the next run erases the
edit. A diff that changes only the source passes where CI regenerates. Verify: each input the
diff adds or changes in the source (`variables.tf`) has a row with the same name, type and default.
A matching block passes, however it was produced.

- Bad: the PR description says "regenerated the terraform-docs Inputs table (`pre-commit run -a`)"
  for a row built by hand.

**Rules repeated from contributor docs.** A rule the README repeats from CONTRIBUTING.md or
RELEASING.md, touched by the change, is edited at its home and the README's copy becomes a
pointer; two edited copies drift. Verify: grep the rule's key words across those files.

- Better than a rewritten copy of the version-bump rule: "See RELEASING.md for when to bump the
  version."

## Opening and first path

**Opening.** After any lifecycle notice, the title and first sentence say what the project or
component gives its users; else readers cannot tell whether it fits. Badges or a logo ahead of it
pass. Verify: read the title, the first prose sentence and the manifest description that copies it.

- Bad: "Dev container Features for our projects" and a bare list. Better: "Dev Container Features
  that add the Go toolchain and golangci-lint to any dev container."

A lifecycle notice (deprecated, moved, archived) comes first and carries its date or version and,
where the project names one, the replacement or where to look.

- Bad: "This project is deprecated." Better: "As of Feb 11th 2020, request is fully deprecated.",
  with a link to the issue on alternatives.

**Shortest path first.** Other setups come after the shortest path to one working result, and
development setup sits under its own heading. Users never pass through development steps,
nor contributors through the user install. Verify: the first install or run block comes before any
heading for another backend, self-hosting, multiple instances, building from source or development.

## Wording that goes stale

- Time-relative wording ("now", "no longer", "moved to", "in the past", "has been removed")
  carries a version or date; else readers cannot tell whether it applies to their version. Verify:
  grep the added lines for those phrases. Bad: "In the past, ripgrep supported a `simd-accel`
  Cargo feature ... support for it has been removed." Better: "Removed in 14.1.1."
- No exact count another file or the tree determines ("the 12-tool surface"); it goes false
  silently. A lower bound growth keeps true ("over 900 rules") passes, as does a checked,
  generated count.
- Keep reasons that change what users do or decide ("takes no options: a value given as an option
  would be saved in the image"); do not raise them as rationale.

## Components

Where users install components separately (plugins, Dev Container Features), each component's
README says how to install or declare it, and any root list says what each gives. Where removal
leaves state (a volume, a config entry), the README says how to remove it; else users cannot
clear what it left. Where removal leaves nothing, ask for no removal section. Where it leaves state
and the project has no removal procedure, the README says what remains; do not ask for invented
removal steps, and expect the PR description to say this was left open. Verify: read install hooks,
scripts, mounts and volume names.

## Templates

A template marks each README line a derived repository must replace or re-point, at the line or in
its setup step; else adopters publish the template's text as their own. A README adopted or synced
from a template drops its pitch and re-points what still applies (badges, licence, links). Verify:
`gh repo view --json isTemplate`; for a derived repository, compare its opening with the template's.

- Bad: a derived action that still opens "Use this template to bootstrap the creation of a
  TypeScript action."

## Package pages

A README that is also a package page (pyproject.toml's `readme`, a `package.json` not marked
`"private": true`, a VS Code extension, a workflow that pushes it to Docker Hub such as
`peter-evans/dockerhub-description`) must render there; else the index shows broken images and
dead links.

- Verify from CI that the release workflow runs `twine check` or `npm pack`; if not, read the
  README for relative links (`](./`, `src="./`). npm's handling of relative links is unconfirmed:
  mark such a finding suspected.
- Docker Hub limits the description to 25,000 bytes (`wc -c README.md`); the common sync action
  truncates to fit.
- Links into docs that differ by version point at the released version.

## Badges and hand copies

- **Badges and offers.** No badge that fails for the README's readers (a private-repo badge, a
  workflow that skips) and no offer for a setup the project says it does not support. Verify:
  `gh repo view --json visibility`; a private repository's public badges fail for readers.
- **Hand copies of reference.** A block pasted from `--help`, an env-var table copied from the
  settings class, or a tree listing restates its source and drifts from it. Offer two fixes: point
  to `--help`, or generate the block. Verify: compare it with `--help` output or the source file.
  A short usage example (the main command and the flags most users need) is not a hand copy; never
  ask to cut one, or the only usage a README has, as restatement. A library whose README is its
  only reference holds no hand copy.
