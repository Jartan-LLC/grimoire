# Reviewing security policy changes

Checks for a change to a security policy (SECURITY.md in `.github/`, the root or `docs/`, or the owner's public
`.github` repository default, which covers every repository without its own). Where the project's own rules, checks or tools
decide a point, raise nothing against them. First review against the lines of `security.md` in the docs-patterns skill
folder (beside SKILL.md, not this file under `references/`), then apply these checks. Unless the PR's purpose is to write
or rewrite the policy, raise only what the change adds or makes false; a public route or a channel that does not work
outside the change is a note, not a finding. Where vulnerability detail may appear is
`information-placement`'s concern, not these checks'.

## The channel

**A public route.** A line that sends reports to a public issue, pull request, discussion or chat discloses the flaw before a fix
exists: Critical. Verify: read every route the file gives ("Please open an issue or send mail" offers one).

**A channel that does not work.** The private channel must work for everyone the file covers, or the reporter finds
no button or a dead service and gives up or goes public: Important. Verify: for GitHub private vulnerability reporting,
`gh api repos/OWNER/REPO/private-vulnerability-reporting` must say `"enabled": true`; for an owner default, check each
public, unarchived repository without its own file (`gh repo list OWNER --limit 1000 --visibility public
--no-archived`, and with `--visibility private` and `internal` for the ones you can read). Private reporting cannot be on in a private or archived repository, so raise nothing about the setting
there, but a policy that covers a private, internal or archived repository must name a channel its readers can use besides
GitHub's form.
Fetch each URL and follow redirects, and check that a named service still takes this project's reports. A mailbox
cannot be checked, but its domain can (`dig +short MX example.org`, then `dig +short A` and `dig +short AAAA` if that is
empty): raise a domain with none of these records, or a null MX (`0 .`), which takes no mail.

- Bad: an owner default saying "click 'Report a vulnerability'" while most repositories it covers have private
  reporting off; "Report on huntr.dev", which stopped taking reports for projects outside AI and ML in 2023.

**Steps for the wrong person.** Steps must name what the reporter sees: "Report a vulnerability" on the security page,
or the `security/advisories/new` link. "New draft security advisory" is the maintainer's button: Minor. A link that works only from inside
GitHub's UI (a redirector that needs a Referer header) fails for a raw read or a mirror: Minor.

**An undocumented channel.** Where private reporting is on but the file names only another channel, reporters split
between two routes or miss one: Minor. Verify with the API call above.

**The file GitHub does not show.** GitHub shows `.github/SECURITY.md`, else the root file, else `docs/`, else the owner
default, which applies only from a public `.github` repository. A change made to a shadowed file and not to the file GitHub shows reaches no reporter: Important. Verify: list each location.

## Supported versions

**Versions that do not match the releases.** A user on an old line reads that they are covered, or a listed version
never existed: Important. Verify: `gh release list -R OWNER/REPO --exclude-drafts --exclude-pre-releases --limit 5` or `git tag -l --sort=-v:refname`; the
current release must be covered, and the README must not contradict the file. A rule tied to releases ("the past two
releases") stays true; raise nothing on it unless the releases break it.

- Bad: `>= 4.11.2 | :white_check_mark:` unchanged since 2021 while releases reached 4.70.1; a table listing `1.3.x` and
  `1.2.1` when the current release is 1.5.2.

## Promises

**A promise with no source.** A response time, fix deadline, disclosure window, bounty, safe harbor or CVE process the
change adds must trace to the policy or another doc at the base branch, the owner's `.github` default, the task, the
linked issue, the PR description or a foundation policy the project adopted; otherwise reporters escalate or disclose on
a schedule nobody runs: Important. Verify: find each one in those places. A
template's numbers ("within 3 working days", "90 day disclosure timeline") are not a source. Raise nothing on a policy
that declines to promise ("we cannot guarantee any specific timeline").

## What a change leaves behind

**References to a removed channel or program.** After a channel or program changes, a line that still points to it
sends the reporter looking for something gone: Important where the policy then names no working channel, else Minor;
leftover terms of a removed program (bounty rules, safe harbor) are Important, as a promise nobody runs.
Verify: search the file for "above", "below", "email", "bounty" and the old channel's name. A README, CONTRIBUTING.md
or other doc line that still gives the old address or service is Important, as a pointer to a missing address is in
`references/contributing.md`; search the tree for it.

- Bad: "let one of the maintainers know at one of the email addresses at the top of this article", after the
  addresses were removed for private reporting; "no longer has a bug bounty program" beside bounty eligibility rules.

**Template text.** Instructions to the author or example rows left in the file: Minor, or as under Supported versions
when the example rows read as real versions. Verify: search for "Use this section to tell people", `$VMTalias`,
`5.1.x`, `4.0.x` and another project's name.

**A retyped report form.** A what-to-include list for a channel that only GitHub's form serves drifts from the form:
Minor. Where email or another channel is also named, a short list is fine. Verify against the repository's `.github/VULNERABILITY_REPORT.yml` (or `.yaml`), else the one in the owner's
`.github` repository (in its `.github` folder), else GitHub's default form (summary, details, proof of concept, impact).
