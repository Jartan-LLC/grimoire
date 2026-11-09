"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/merge"
COMMITS = json.loads(
    '[{"subject": "feat(dotmerge): merge the team settings at container start", "body": "The user\'s values win; the original is kept as settings.json.pre-dotmerge.", "files": {"src/dotmerge/install.sh": "#!/bin/sh\\n# Merge the image settings into the user\'s settings.json.\\nset -eu\\nCONF=\\"$HOME/.config/tool/settings.json\\"\\ncp \\"$CONF\\" \\"$CONF.pre-dotmerge\\"\\npython3 /usr/local/share/dotmerge/merge.py \\"$CONF\\"\\n"}}, {"subject": "fix(dotmerge): never replace an existing settings.json.pre-dotmerge", "body": "A second start overwrote the user\'s original with the merged file.", "files": {"src/dotmerge/install.sh": "#!/bin/sh\\n# Merge the image settings into the user\'s settings.json.\\nset -eu\\nCONF=\\"$HOME/.config/tool/settings.json\\"\\n[ -e \\"$CONF.pre-dotmerge\\" ] || cp \\"$CONF\\" \\"$CONF.pre-dotmerge\\"\\npython3 /usr/local/share/dotmerge/merge.py \\"$CONF\\"\\n"}}, {"subject": "fix(dotmerge): keep a leftover held copy beside its file at deactivation", "body": "An interrupted merge leaves settings.json.held; deactivation now leaves it in place instead of deleting it.", "files": {"src/dotmerge/deactivate.sh": "#!/bin/sh\\n# settings.json.held from an interrupted merge stays beside its file.\\nset -eu\\n"}}, {"subject": "fix(dotmerge): follow a symlinked settings.json", "body": "Dotfile managers link the file; the merge replaced the link with a plain file.", "files": {"src/dotmerge/merge.py": "\\"\\"\\"Merge team settings into the user\'s file, following a symlink.\\"\\"\\"\\n"}}, {"subject": "fix(dotmerge): leave a settings.json that is not valid JSON untouched", "body": "It now prints `dotmerge: settings.json is not valid JSON; left as is` and stops.", "files": {"src/dotmerge/merge.py": "\\"\\"\\"Merge team settings into the user\'s file, following a symlink.\\n\\nA file that is not valid JSON is left as is, with a message.\\n\\"\\"\\"\\n"}}]'
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
