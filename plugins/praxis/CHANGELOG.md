# Changelog

## 2.1.0

- New `/praxis:review-cycle` command: takes a branch through review rounds until two in a row find nothing Critical or Important, runs a closing round on the change's words, then opens its PR as a draft and stops for you to mark it ready. Each round fixes what has one clear fix and brings you each real judgment call; tell it you won't be around, or to decide, and it decides those calls itself, each in a commit of its own, and lists them for you when the PR opens, with anything it left for you, such as repo settings. Your agent pushes the branch after every round, force-pushes only to update a stack as `gitwise:github-conventions` says, and resumes a cycle from the branch folder's `cycle.md`.
- `review-pr` tells its reviewers nothing about what to look for or what earlier reviews found, and a review you limit to part of a change runs only the reviewers for that part.

## 2.0.0

- Needs gitwise 2.0.0 or later.
- Breaking: the `issue-planner` agent is removed. Run `/praxis:plan-issue` instead, which explores the codebase and writes the plan itself. In Codex, the installed `issue-planner` role stays until you delete it: remove `issue-planner.toml` from `~/.codex/agents/grimoire/<version>/` (`$CODEX_HOME/agents/grimoire/<version>/` if you set `CODEX_HOME`), where `<version>` is the praxis version you upgraded from, such as `1.12.0`, and from any other version directory there that holds one.
- `plan-issue` writes shorter plans in a new format: Approach, Decisions for the user, Out of scope, Steps and Verification. A plan no longer restates the issue or rates its complexity. praxis now carries the format itself instead of reading it from gitwise.

## 1.12.0

- Needs gitwise 1.5.0 or later.
- `implement-issue` branches from an open PR's branch when the issue builds on that PR's unmerged work.
- `create-pr` bases a PR on the branch it was cut from, or asks you when it cannot tell, and opens and links a stacked PR as `gitwise:github-conventions`' `stacks.md` says.
- `plan-issue` says that sub-issues that build on each other may branch from each other's branches, as `stacks.md` says, and still merge into the parent feature branch.
- `information-placement`'s stacked-PR example now says that merging a PR also merges the PRs below it in its stack.

## 1.11.0

- `review-pr` reviews a branch that has no PR yet (`/praxis:review-pr <branch>`, or the current branch): it diffs the branch against the base you name, or the branch it was cut from, names that base in the review, and takes the PR title and description from the branch's `pr.md` in the workspace when there is one. Its reviewers read the branch's files from a checkout of it: when the branch is checked out elsewhere, your agent uses that checkout or adds a worktree, and never switches another checkout's branch, and the review says when it left out uncommitted changes.
- `address-review` works from such a review, keeping the title and description in `pr.md` until the PR exists, and `create-pr` takes them from `pr.md` when the branch has one.

## 1.10.0

- New `workspace-patterns` skill: where your agent keeps its working files. Each effort gets a folder in the main checkout's `.claude/workspace/` (`issue-<n>/`, or a name chosen when the work starts), also when your agent works in a worktree, with a subfolder per branch (`feature/x` -> `feature--x`, or `pr-<n>` for a PR from a fork); worktrees go in `.claude/worktrees/`. Where git does not ignore these, your agent asks before changing your `.gitignore`.
- `plan-issue` saves the plan as `.claude/workspace/issue-<n>/plan.md` (was `issue-<n>-plan.md`), and `implement-issue` and `create-pr` read it there. `review-pr` saves each review as the next numbered file in the PR branch's folder (`1.md`, `2.md`, ...) instead of replacing `pr-<n>-review.md`, and `address-review` reads the latest. Plans and reviews at the old paths are still read.

## 1.9.0

- Needs gitwise 1.4.0 or later.
- `create-pr` opens a draft pull request, and it stays a draft until it is marked ready. Your agent is told to mark it ready when it is ready for someone else to review or merge, but does not always: some models often leave it a draft when you say the work is done without asking for the PR to be marked ready. If it leaves the PR a draft, run `gh pr ready` yourself.

## 1.8.0

- Needs gitwise 1.3.0 or later.
- `implement-issue` reads `comment-hygiene`'s new `writing.md` before your agent writes code: it writes what the code cannot say (a reason, a hazard, the spec or issue the code follows, what a caller needs that the signature does not give, what a new file owns), leaves out what the code, the signature or another file already says and the story of the change, gives reasons rather than ticket ids, and updates comments the change makes false.
- `general-reviewer` raises a comment or docstring that misleads (stale, contradicting the code, or describing as present something that is gone) as Important, as `review-severity` now says. Retold facts and comments stating a fact another file owns stay Important; other comments that don't earn their place are now Minor.
- `code-hygiene`, `code-structure`, `comment-hygiene`, `docs-patterns`, `logging-patterns` and `readable-code` no longer point your agent to pythonica, which may not be installed.
- New `plain-writing` skill for prose that informs: docs, READMEs, explanation pages, answers, emails, release notes, and requests to make text clearer. Your agent decides what a reader needs before it writes, keeps warnings, conditions, exact commands and prerequisites, cuts filler and wordiness, writes in a plain voice without asides, opinions or claims your sources do not support (and no first person in documents), and finishes with one pass over the wording. In an existing file it changes only the text it writes, and keeps the file's own dashes, quotes and heading case, unless you ask it to make the file clearer. It does not apply to blog posts, essays, site copy or personal writing, which go to `voiced-writing` (a personal letter sent by email included; a release announcement posted as a blog post and a docs site's home page stay with `plain-writing`), or to commit messages or PR text, and `comment-hygiene` still decides whether a code comment should exist; the prose of the comments and docstrings that stay is in scope.
- New `voiced-writing` skill for blog posts, essays, opinion pieces, personal writing and site copy. Your agent takes the voice from posts or pages already on the site or from a sample you give, keeps your opinions, asides, hedges, quotes and contractions, adds no fact, relationship, opinion, advice or lesson your notes or brief do not give, writes prose instead of lists of takeaways, and finishes with a pass over `plain-writing`'s wording patterns in which your voice wins. `review-pr`'s `doc-reviewer` still judges a changed blog post or page by `plain-writing`.
- New `information-placement` skill: where each kind of information belongs -- the commit message, the PR description, a code comment or docstring, the README, the changelog, a docs page, an issue, or nowhere -- and what no text may hold whatever your project says: narration of the session or the review rounds, claims that need their links to make sense, pointers a reader cannot open (a path on the author's machine, an ignored file, a session link), restated file lists and CI totals, hand-kept copies of what the code declares, adopter text left in a repository made from a template, and exploit detail of a vulnerability whose fix is not released, in public text other than the commit message whose change removes the flaw or text that links the released fix or a public advisory. Your project's own rules move any default home: by default, answers to review findings go in the fix and the PR description, and plans and findings made during the work stay in your workspace. Your agent also uses it when you ask where something should go.
- `doc-reviewer` runs on every PR and checks where information sits with `information-placement`, in the PR title, the PR description and the commit messages, which `review-pr` hands it, and in changed documents and changelogs; exploit detail outside those exceptions is a Critical finding, narration and claims or pointers a reader cannot follow Important, restatements, hand-kept copies and leftover template text Minor, and information outside its usual home Minor unless it misleads a reader or leaves them without what they need.
- `plain-writing`'s `references/patterns.md` is licensed CC BY-SA 4.0, as an adaptation of Wikipedia's Signs of AI writing; the rest of praxis stays MIT.
- Your agent loads `plain-writing` alongside `docs-patterns` when it writes or reviews a document, and `implement-issue`'s documentation step loads both. The "brevity is paramount" rule is gone; `plain-writing`'s keep and cut lists replace it.
- `doc-reviewer` judges bloat by those lists and no longer flags a document for its length alone, except where a tool truncates that type of file, as with a long agent instruction file.
- `doc-reviewer` files filler and wordiness inside a passage that stays as a Minor finding.
- `create-pr` no longer comments on the issue that a pull request was created, or on the PR itself.
- `review-pr` no longer posts its review on the PR: it saves it to `.claude/workspace/pr-<number>-review.md` and shows it to you, so the people watching the PR are not notified of it. `address-review` reads it there, along with the comments people posted, and no longer posts a comment answering each round: it states declined findings and fixes made differently as decisions in the PR description, and replies on the PR only to a finding a person posted that it declined, fixed differently or found already the case, in the line's thread when the finding was posted on a line. It also reads the comments people leave on a PR's lines, which it used to miss.
- `plan-issue` saves the plan in `.claude/workspace/` and no longer posts it on the issue, and `implement-issue` no longer posts an "Implementation Complete" comment, so the people watching your issues are not notified of either. The plan goes to `.claude/workspace/issue-<issue-number>-plan.md`, and `implement-issue` and `create-pr` read it there as well as from the issue's comments.
- `create-pr` flags in the PR description where the change departs from the issue's plan.
- Where your project has no release document, CONTRIBUTING.md or other contributor docs, your agent asks you before creating CONTRIBUTING.md or contributor docs to hold the release procedure, and says in the PR description that you approved it.
- Where your project keeps no changelog, `implement-issue` has your agent state in the commit message a change consumers see and any step they must take to upgrade.
- Where your project lacks a document a change would go in, such as a changelog or a README, `doc-reviewer` asks you once, as a Minor question, whether you want one, instead of filing the missing entry against the change. It also accepts a new CONTRIBUTING.md the PR description says you approved.
- `general-reviewer` reads AGENTS.md as well as CLAUDE.md for your project's rules, and `implement-issue` takes the Verify commands from either.
- `address-review` reads `comment-hygiene`'s `writing.md` before a fix edits code, and the matching `docs-patterns` file before a fix edits a document, as `implement-issue` does.
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
