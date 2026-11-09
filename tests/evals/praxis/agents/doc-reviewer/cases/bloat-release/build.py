"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/release-tags"
COMMITS = json.loads(
    '[{"subject": "feat(release): tag each untagged package version", "body": "scripts/tag-release.sh tags <name>--v<version> and pushes.", "files": {"scripts/tag-release.sh": "#!/bin/sh\\n# Tag each package version that has no tag yet, then push the tags.\\nset -eu\\nmake verify\\n"}}, {"subject": "fix(release): say how to recover from a 403 on push", "body": "A token issued before a workflow file changed is refused with HTTP 403; gh auth refresh -s workflow fixes it.", "files": {"scripts/tag-release.sh": "#!/bin/sh\\n# Tag each package version that has no tag yet, then push the tags.\\nset -eu\\nmake verify\\n# On HTTP 403 after a workflow change: gh auth refresh -s workflow, then rerun.\\n"}}, {"subject": "fix(release): skip versions from before per-package changelogs", "body": "1.5.0 and earlier have no changelog section to tag from.", "files": {"scripts/tag-release.sh": "#!/bin/sh\\n# Tag each package version that has no tag yet, then push the tags.\\nset -eu\\nmake verify\\n# On HTTP 403 after a workflow change: gh auth refresh -s workflow, then rerun.\\n# Versions 1.5.0 and earlier predate per-package changelogs and are skipped.\\n"}}, {"subject": "fix(verify): accept caret, tilde, equals and exact ranges", "body": "make verify rejected `=1.2.0`.", "files": {"scripts/check_ranges.py": "\\"\\"\\"Accept ^, ~, = and exact version ranges.\\"\\"\\"\\n"}}, {"subject": "fix(release): stop waiting for the dev container build", "body": "The tag push no longer waits for it.", "files": {"scripts/tag-release.sh": "#!/bin/sh\\n# Tag each package version that has no tag yet, then push the tags.\\nset -eu\\nmake verify\\n# On HTTP 403 after a workflow change: gh auth refresh -s workflow, then rerun.\\n# Versions 1.5.0 and earlier predate per-package changelogs and are skipped.\\n# The dev container build is not waited for.\\n"}}, {"subject": "docs: describe the change", "body": "", "files": {"RELEASING.md": "# Releasing\\n\\nEach package carries its version in `pyproject.toml`. Bump it in the PR that changes the package,\\nwith an entry in its `CHANGELOG.md`.\\n\\n## Tag a release\\n\\nAfter the PR merges, run `make test`, then `scripts/tag-release.sh` from `main`. It tags each\\npackage whose version is not tagged yet, as `<name>--v<version>`, and pushes the tags. If the push\\nfails with HTTP 403 after a workflow file changed, run `gh auth refresh -s workflow` and run it\\nagain. Versions from before per-package changelogs (1.5.0 and earlier) are skipped. `make verify`\\naccepts `^`, `~`, `=` and exact dependency ranges. The script does not wait for the dev container\\nbuild.\\n"}}]'
)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for commit in COMMITS:
    for path, text in commit["files"].items():
        target = pathlib.Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git("add", "-A")
    git("commit", "-q", "-m", commit["subject"], "-m", commit["body"])
