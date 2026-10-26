"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def commit(subject: str, body: str = "") -> None:
    git("add", "-A")
    git("commit", "-q", "-m", subject, *(["-m", body] if body else []))


def push_to_origin(*branches: str) -> None:
    git("init", "-q", "--bare", "../origin.git")
    git("remote", "add", "origin", "../origin.git")
    git("push", "-q", "-u", "origin", *branches)


git("checkout", "-q", "-b", "feature/sentences")
write(
    "textstats/sentences.py",
    '"""Sentence counts."""\n\nimport re\n\n\ndef sentence_count(text: str) -> int:\n    """Sentences in `text`, ended by ., ! or ?."""\n    return len([s for s in re.split(r"[.!?]+", text) if s.strip()])\n',
)
write(
    "tests/test_sentences.py",
    'from textstats.sentences import sentence_count\n\n\ndef test_counts() -> None:\n    assert sentence_count("Hi. Bye!") == 2\n',
)
commit(
    "feat(textstats): count sentences",
    "Readability scores need a sentence count beside the word count.",
)
