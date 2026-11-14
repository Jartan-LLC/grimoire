import json

from diskreport import cli


def test_json_has_used_pct(capsys):
    cli.main(["--json"])
    row = json.loads(capsys.readouterr().out)[0]
    assert row["mount"] == "/" and 0 <= row["used_pct"] <= 100
