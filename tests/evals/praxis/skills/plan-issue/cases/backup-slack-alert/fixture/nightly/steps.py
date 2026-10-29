"""The backup's steps, each a shell command."""

import subprocess


class StepFailed(RuntimeError):
    """A step exited non-zero."""


def run_step(name: str, argv: list[str]) -> None:
    """Run one step, raising StepFailed with its stderr when it fails."""
    done = subprocess.run(argv, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise StepFailed(f"{name} failed ({done.returncode}): {done.stderr.strip()[-500:]}")


def backup_steps(day: str) -> list[tuple[str, list[str]]]:
    """The steps for one night's backup, in order."""
    dump = f"/var/backups/app-{day}.sql"
    return [
        ("dump", ["pg_dump", "--file", dump, "app"]),
        ("compress", ["gzip", "-f", dump]),
        ("upload", ["aws", "s3", "cp", f"{dump}.gz", f"s3://acme-backups/app/{day}.sql.gz"]),
    ]
