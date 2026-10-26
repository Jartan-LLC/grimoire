"""The external commands the runner starts, resolved once, and the one place it starts them."""

import shutil
import subprocess
from typing import Any

GIT = shutil.which("git") or "git"
CLAUDE = shutil.which("claude") or "claude"
UV = shutil.which("uv") or "uv"


def run(args: list[str], **options: Any) -> subprocess.CompletedProcess[Any]:
    """`subprocess.run` on an argument list this package built; nothing goes through a shell.

    Callers pass `check` themselves: a `claude` session that fails is still a sample.
    """
    # Typed as Any: forwarded keyword options defeat subprocess.run's overloads.
    start: Any = subprocess.run
    return start(args, **options)
