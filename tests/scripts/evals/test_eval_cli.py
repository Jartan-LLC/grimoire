import pathlib

import eval as cli
from evals.suite import load_suite
from evals.verdict import MetricVerdict
from helpers import SUITE, write_suite


def test_record_baseline_replaces_only_its_own_model_and_arm(tmp_path: pathlib.Path) -> None:
    key = tmp_path / "key.toml"
    key.write_text('split = "dev"\n\n[[check]]\nmetric = "kept"\n')
    cli.record_baseline(key, "claude-opus-5-5", "none", 3, 3)
    cli.record_baseline(key, "claude-haiku-5-5", "none", 1, 3)
    cli.record_baseline(key, "claude-opus-5-5", "none", 2, 3)
    text = key.read_text()
    assert text.count("[[baseline]]") == 2
    assert 'model = "claude-opus-5-5"\narm = "none"\nfailures = 2\n' in text
    assert 'model = "claude-haiku-5-5"\narm = "none"\nfailures = 1\n' in text
    assert text.startswith('split = "dev"\n\n[[check]]')


def test_a_watch_model_reports_harm_without_failing_a_bar(tmp_path: pathlib.Path) -> None:
    suite = load_suite(
        write_suite(
            tmp_path,
            SUITE + '\n[[metric]]\nid = "no_exploit"\ndirection = "higher"\nmust_hold = true\n',
        )
    )
    verdicts = {
        "kept": MetricVerdict("kept", 6, 1, 0.5, 0, 3, 1, 0.01, "WORSE"),
        "no_exploit": MetricVerdict("no_exploit", 2, 1, 0.9, 0, 1, 1, 0.5, "WORSE", must_hold=True),
    }
    gate = cli.report(suite, verdicts, "HURT", "", watch=False)
    watch = cli.report(suite, verdicts, "HURT", "", watch=True)
    assert [line.split(":")[0] for line in gate[:2]] == ["FAILED", "FAILED"]
    assert watch[0].startswith("REPORT: kept WORSE")
    assert watch[1].startswith("STANDING: no_exploit WORSE")
    assert any(line.startswith("Result (watch model, advisory") for line in watch)
