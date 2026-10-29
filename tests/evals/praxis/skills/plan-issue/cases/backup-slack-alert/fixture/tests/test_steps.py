import pytest

from nightly.steps import StepFailed, backup_steps, run_step


def test_steps_run_in_order():
    assert [name for name, _ in backup_steps("2026-10-01")] == ["dump", "compress", "upload"]


def test_failed_step_raises_with_stderr():
    with pytest.raises(StepFailed, match="boom"):
        run_step("x", ["python3", "-c", "import sys; sys.stderr.write('boom'); sys.exit(3)"])
