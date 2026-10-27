"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/column-flag", "subject": "feat(cli): total any column with --column", "body": "Finance wants the tax column totalled as well as the amount.", "files": {"tally/cli.py": "\\"\\"\\"The `tally` command.\\"\\"\\"\\n\\nimport argparse\\nimport pathlib\\n\\nfrom tally.report import total\\n\\n\\ndef main(argv: list[str] | None = None) -> int:\\n    \\"\\"\\"Print the total of one column of an export file.\\"\\"\\"\\n    parser = argparse.ArgumentParser(prog=\\"tally\\")\\n    parser.add_argument(\\"export\\", type=pathlib.Path)\\n    parser.add_argument(\\"--column\\", default=\\"amount\\")\\n    args = parser.parse_args(argv)\\n    # parse_rows strips a UTF-8 BOM and skips blank lines, so the text needs no cleanup here.\\n    print(total(args.export.read_text(), args.column))\\n    return 0\\n"}, "rename": null}'
)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("init", "-q", "--bare", "../origin.git")
git("remote", "add", "origin", "../origin.git")
git("push", "-q", "-u", "origin", "main")
git("checkout", "-q", "-b", CHANGE["branch"])
if CHANGE["rename"]:
    git("mv", *CHANGE["rename"])
for path, text in CHANGE["files"].items():
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
git("add", "-A")
git("commit", "-q", "-m", CHANGE["subject"], "-m", CHANGE["body"])
