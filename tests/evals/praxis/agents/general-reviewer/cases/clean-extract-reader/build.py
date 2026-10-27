"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/read-export", "subject": "refactor(cli): read the export through one helper", "body": "The upcoming `tally diff` command reads two exports the same way.", "files": {"tally/cli.py": "\\"\\"\\"The `tally` command.\\"\\"\\"\\n\\nimport argparse\\nimport pathlib\\n\\nfrom tally.report import total\\n\\n\\ndef read_export(path: pathlib.Path) -> str:\\n    \\"\\"\\"The text of the export at `path`.\\"\\"\\"\\n    return path.read_text(encoding=\\"utf-8\\")\\n\\n\\ndef main(argv: list[str] | None = None) -> int:\\n    \\"\\"\\"Print the total of an export file.\\"\\"\\"\\n    parser = argparse.ArgumentParser(prog=\\"tally\\")\\n    parser.add_argument(\\"export\\", type=pathlib.Path)\\n    args = parser.parse_args(argv)\\n    print(total(read_export(args.export)))\\n    return 0\\n", "tests/test_cli.py": "import pathlib\\n\\nfrom tally.cli import main\\n\\n\\ndef test_main_prints_the_total(tmp_path: pathlib.Path, capsys) -> None:\\n    export = tmp_path / \\"export.csv\\"\\n    export.write_text(\\"sku,amount\\\\na,1.50\\\\n\\", encoding=\\"utf-8\\")\\n    assert main([str(export)]) == 0\\n    assert capsys.readouterr().out.strip() == \\"1.50\\"\\n"}, "rename": null}'
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
