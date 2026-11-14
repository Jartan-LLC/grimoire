"""Run each job in turn, carrying on past a failure."""

from collections.abc import Callable


def run_jobs(jobs: dict[str, Callable[[], None]]) -> list[str]:
    """Run every job; return the names of the ones that failed."""
    failed = []
    for name, job in jobs.items():
        print("starting", name)
        try:
            job()
        except Exception as error:
            print("FAILED", name, error)
            failed.append(name)
        else:
            print("done", name)
    return failed
