# Changelog

## 1.8.0

- Needs gitwise 1.3.0 or later.
- `code-hygiene`, `code-structure`, `comment-hygiene`, `docs-patterns`, `logging-patterns` and `readable-code` no longer point your agent to pythonica, which may not be installed.
- New `plain-writing` skill for prose that informs: docs, READMEs, explanation pages, answers, emails, release notes, and requests to make text clearer. Your agent decides what a reader needs before it writes, keeps warnings, conditions, exact commands and prerequisites, cuts filler and wordiness, writes in a plain voice without asides, opinions or claims your sources do not support (and no first person in documents), and finishes with one pass over the wording. In an existing file it changes only the text it writes, and keeps the file's own dashes, quotes and heading case, unless you ask it to make the file clearer. It does not apply to blog posts, essays, site copy or personal writing, which go to `voiced-writing` (a personal letter sent by email included; a release announcement posted as a blog post and a docs site's home page stay with `plain-writing`), or to commit messages or PR text, and `comment-hygiene` still decides whether a code comment should exist; the prose of the comments and docstrings that stay is in scope.
- New `voiced-writing` skill for blog posts, essays, opinion pieces, personal writing and site copy. Your agent takes the voice from posts or pages already on the site or from a sample you give, keeps your opinions, asides, hedges, quotes and contractions, adds no fact, relationship, opinion, advice or lesson your notes or brief do not give, writes prose instead of lists of takeaways, and finishes with a pass over `plain-writing`'s wording patterns in which your voice wins. `review-pr`'s `doc-reviewer` still judges a changed blog post or page by `plain-writing`.
- New `information-placement` skill: where each kind of information belongs -- the commit message, the PR description, a code comment or docstring, the README, the changelog, a docs page, an issue, or nowhere -- and what no text may hold whatever your project says: narration of the session or the review rounds, claims that need their links to make sense, pointers a reader cannot open (a path on the author's machine, an ignored file, a session link), restated file lists and CI totals, hand-kept copies of what the code declares, adopter text left in a repository made from a template, and exploit detail of a vulnerability whose fix is not released, in public text. Your project's own rules move any default home. Your agent also uses it when you ask where something should go.
- `doc-reviewer` runs on every PR and checks where information sits with `information-placement`, in the PR title, the PR description and the commit messages, which `review-pr` hands it, and in changed documents and changelogs; exploit detail is a Critical finding, narration and claims or pointers a reader cannot follow Important, restatements, hand-kept copies and leftover template text Minor, and information outside its usual home Minor unless it misleads a reader or leaves them without what they need.
- `plain-writing`'s `references/patterns.md` is licensed CC BY-SA 4.0, as an adaptation of Wikipedia's Signs of AI writing; the rest of praxis stays MIT.
- Your agent loads `plain-writing` alongside `docs-patterns` when it writes or reviews a document, and `implement-issue`'s documentation step loads both. The "brevity is paramount" rule is gone; `plain-writing`'s keep and cut lists replace it.
- `doc-reviewer` judges bloat by those lists and no longer flags a document for its length alone, except where a tool truncates that type of file, as with a long agent instruction file.
- `doc-reviewer` files filler and wordiness inside a passage that stays as a Minor finding.
- `create-pr` no longer comments on the issue that a pull request was created, or on the PR itself.
- `review-pr` no longer posts its review on the PR: it saves it to `.claude/workspace/pr-<number>-review.md` and shows it to you, so the people watching the PR are not notified of it. `address-review` reads it there, along with the comments people posted, and no longer posts a comment answering each round: it states declined findings and fixes made differently as decisions in the PR description, and replies on the PR only to a finding a person posted that it declined or fixed differently.
- `information-placement` gives each answer to a review finding its home in the fix or in the PR description, keeps plans and findings made during the work in your workspace, and raises "Changed in review" lines in a PR description as narration.
- `plan-issue` saves the plan in `.claude/workspace/` and no longer posts it on the issue, and `implement-issue` no longer posts an "Implementation Complete" comment, so the people watching your issues are not notified of either. The plan goes to `.claude/workspace/issue-<issue-number>-plan.md`, and `implement-issue` and `create-pr` read it there as well as from the issue's comments.
- `create-pr` flags in the PR description where the change departs from the issue's plan.
- `create-issue` writes the issue's title and body by `gitwise:github-conventions`' new issue rules.
- `docs-patterns` has rules for docs pages (how-to, reference, explanation and tutorial pages, runbooks, operator guides, architecture pages, the home page), and `implement-issue` searches docs pages for what a change makes false and reads the rules before editing one: your agent writes for the release your readers install, marks planned state where it states it, gives each page one reader and its scope, orders a how-to's steps as the reader does them, and ends each runbook scenario that contains a problem with the step that undoes the containment. `doc-reviewer` checks a changed page against them.
- When existing docs break a `docs-patterns`, `plain-writing` or `information-placement` rule, your agent follows the rule instead of matching them, and `doc-reviewer` no longer raises that departure.
- `docs-patterns` has rules for security policies (SECURITY.md, including an owner's default), and `implement-issue` reads them before editing one: your agent names a private reporting channel that works for every repository the policy covers, states supported versions as a rule tied to releases, promises no response time, deadline, bounty or safe harbor your maintainers have not chosen, and asks you before writing a channel, promise or version rule your project has not settled. `doc-reviewer` checks a changed security policy against them, raising a public reporting route as Critical.
- `comment-hygiene` and `docs-patterns` no longer point to `gitwise:commit-pr-writing` for other merge settings.
- `doc-reviewer` raises a claim your sources do not support (inflated significance, borrowed authority, guesses, unverifiable praise) as an Important finding.

## 1.7.0

- `docs-patterns` has rules for READMEs, CONTRIBUTING.md, release procedures such as RELEASING.md, changelog entries and release notes, and agent instruction files such as CLAUDE.md and AGENTS.md. When it writes CONTRIBUTING.md, a release procedure or an agent instruction file, your agent asks you before adding a convention your project has not settled; when nobody can answer, it leaves the convention out and says so in the PR description.
- `implement-issue` searches your READMEs and agent instruction files for what the change makes false, updates CONTRIBUTING.md, the release procedure and the changelog where the change touches them, and reads that document's rules before writing it.
- `doc-reviewer` checks a changed README, CONTRIBUTING.md, release procedure, changelog or agent instruction file against that document's review checks, and its summary names the reference files it applied.

## 1.6.0

- Needs gitwise 1.2.0 or later.
- `plan-issue`, `implement-issue`, `create-pr` and `review-pr` no longer end the comment they post with a hint naming the next `/praxis:` command to run, or with a "Generated by Claude" footer.
- `implement-issue`, `create-pr` and `address-review` load `gitwise:commit-pr-writing` before writing a commit message, a PR title or a PR description. Commit messages, review fixes included, give the reason for the change instead of a list of edits and say nothing about review rounds; PR descriptions brief the reviewer.
- `address-review` checks the PR title and description against the change at the start and at the end of every round, and answers the round in one PR comment, declined findings and findings that already held included, and records each declined finding even when a round makes no commit. `implement-issue` does the same check after pushing to a branch that already has a PR.
- `comment-hygiene` and `docs-patterns` send a change's reason to the commit message instead of the PR body.
- `create-pr`, `address-review` and `implement-issue` follow your project's own rules where they differ.

## 1.5.3

No user-visible change.

## 1.5.2

- `comment-hygiene`: a standing hot-path measurement stays inline as a WHY; only
  a change's before/after numbers go to the PR body. The density re-read now
  presumes each comment goes unless the skill's own rules keep it.

## 1.5.1

- No user-visible change.

## 1.5.0

- New `comment-hygiene` skill: the comment rules (what to keep, delete or
  exempt; tombstones; retold facts; comment density) and
  `find-duplicate-comments.js` move out of `code-hygiene`, which keeps dead and
  duplicated code, naming, real implementations and scoped suppressions. The
  general reviewer loads both.
