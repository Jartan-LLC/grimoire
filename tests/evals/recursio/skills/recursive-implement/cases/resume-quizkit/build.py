"""Build this case's history: run by the eval runner inside the fixture repository.

A walk-away run that stopped after its first wave: the shared types, both wave 1 parts with their
tests, and split.md recording wave 1 passed and waves 2 and 3 pending, all left uncommitted.
"""

import pathlib

FILES = {
    "src/quizkit/__init__.py": r'''"""quizkit: mark multiple-choice quizzes."""
''',
    "src/quizkit/model.py": r'''"""Shared types for quizkit: questions, responses and the error."""

from dataclasses import dataclass


class QuizError(ValueError):
    """A question bank, a responses file or a request that cannot be used."""


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    choices: tuple[str, ...]
    answer: frozenset[int]
    points: int


@dataclass(frozen=True)
class Response:
    student: str
    question: str
    chosen: frozenset[int]
''',
    "src/quizkit/bank.py": r'''"""Parse a question bank."""

import re

from quizkit.model import Question, QuizError

HEAD = re.compile(r"^(\S+?)(?: \((\d+) points?\))?: (.+)$")


def _finish(found: list[Question], ids: set[str], head: tuple[int, str, str, int] | None,
            choices: list[tuple[str, bool]]) -> None:
    if head is None:
        return
    number, qid, text, points = head
    if len(choices) < 2:
        raise QuizError(f"line {number}: {qid} needs at least two choices")
    answer = frozenset(i for i, (_, right) in enumerate(choices) if right)
    if not answer:
        raise QuizError(f"line {number}: {qid} has no correct choice")
    if qid in ids:
        raise QuizError(f"line {number}: {qid} is used twice")
    ids.add(qid)
    found.append(Question(qid, text, tuple(c for c, _ in choices), answer, points))


def parse_bank(text: str) -> list[Question]:
    """The questions of a bank, in file order."""
    found: list[Question] = []
    ids: set[str] = set()
    head: tuple[int, str, str, int] | None = None
    choices: list[tuple[str, bool]] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if not line:
            _finish(found, ids, head, choices)
            head, choices = None, []
        elif head is not None and line[:2] in ("* ", "- "):
            choices.append((line[2:].strip(), line[0] == "*"))
        elif head is None and (match := HEAD.match(line)):
            head = (number, match[1], match[3], int(match[2] or 1))
        else:
            raise QuizError(f"line {number}: cannot read {line!r}")
    _finish(found, ids, head, choices)
    return found
''',
    "src/quizkit/scoring.py": r'''"""Read responses and score them."""

from quizkit.model import Question, QuizError, Response


def parse_responses(text: str, bank: list[Question]) -> list[Response]:
    """The responses in file order, checked against the bank."""
    questions = {q.id: q for q in bank}
    seen: set[tuple[str, str]] = set()
    rows: list[Response] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if number == 1 or not line.strip():
            continue
        fields = [f.strip() for f in line.split(",")]
        if len(fields) != 3:
            raise QuizError(f"line {number}: expected student,question,chosen")
        student, qid, letters = fields
        if qid not in questions:
            raise QuizError(f"line {number}: unknown question {qid}")
        chosen = frozenset(ord(letter) - ord("A") for letter in letters.upper())
        if any(not 0 <= i < len(questions[qid].choices) for i in chosen):
            raise QuizError(f"line {number}: {qid} has no choice {letters}")
        if (student, qid) in seen:
            raise QuizError(f"line {number}: {student} answered {qid} twice")
        seen.add((student, qid))
        rows.append(Response(student, qid, chosen))
    return rows


def score(question: Question, response: Response) -> int:
    """Full points for exactly the correct choices, otherwise none."""
    return question.points if response.chosen == question.answer else 0


def totals(bank: list[Question], responses: list[Response]) -> dict[str, int]:
    """Each student's points, in name order."""
    questions = {q.id: q for q in bank}
    points: dict[str, int] = {}
    for response in responses:
        points[response.student] = points.get(response.student, 0) + score(questions[response.question], response)
    return dict(sorted(points.items()))
''',
    "tests/test_bank.py": r'''"""Tests for quizkit.bank."""

import pytest

from quizkit.bank import parse_bank
from quizkit.model import QuizError


def test_points_default_to_one():
    (question,) = parse_bank("Q9: Pick b\n- a\n* b\n")
    assert (question.id, question.points, question.answer) == ("Q9", 1, frozenset({1}))


@pytest.mark.parametrize(
    "text",
    ["Q1: one\n* a\n", "Q1: none right\n- a\n- b\n", "Q1: a\n* a\n- b\n\nQ1: again\n* a\n- b\n", "just words\n"],
)
def test_bad_banks_name_a_line(text):
    with pytest.raises(QuizError, match=r"^line \d+: "):
        parse_bank(text)
''',
    "tests/test_scoring.py": r'''"""Tests for quizkit.scoring."""

import pytest

from quizkit.model import Question, QuizError, Response
from quizkit.scoring import parse_responses, score, totals

BANK = [Question("Q1", "t", ("a", "b", "c"), frozenset({0, 1}), 2), Question("Q2", "t", ("a", "b"), frozenset({1}), 1)]


def test_letters_become_choice_numbers():
    rows = parse_responses("student,question,chosen\nzed,Q1,ba\nzed,Q2,\n", BANK)
    assert rows == [Response("zed", "Q1", frozenset({0, 1})), Response("zed", "Q2", frozenset())]


def test_only_the_exact_answer_scores():
    assert score(BANK[0], Response("zed", "Q1", frozenset({0}))) == 0
    assert score(BANK[0], Response("zed", "Q1", frozenset({0, 1}))) == 2


def test_totals():
    rows = parse_responses("student,question,chosen\nyan,Q2,B\nab,Q1,AB\nab,Q2,A\n", BANK)
    assert totals(BANK, rows) == {"ab": 2, "yan": 1}


@pytest.mark.parametrize("row", ["zed,Q7,A", "zed,Q2,C", "zed,Q1,A\nzed,Q1,B"])
def test_bad_rows(row):
    with pytest.raises(QuizError, match="line"):
        parse_responses(f"student,question,chosen\n{row}\n", BANK)
''',
    ".claude/workspace/quizkit/split.md": r"""If the splitting skill was lost to compaction, load `recursio:splitting-implementation` again and resume from the status lines below.

# Split: quizkit

## Settled decisions

- Shared types in `src/quizkit/model.py`: `Question`, `Response` and `QuizError` -- source: the README.
- Each module's own tests in `tests/test_<module>.py`, run with `python3 -m pytest -q tests/test_<module>.py` -- source: decided here.
- A blank response is not an answer: it scores 0 and is left out of the share who answered -- source: the README.

## Wave 1

Snapshot before spawning: no changed files; contract hashes: src/quizkit/model.py f67babf1563d31b730c9371d54f446d5220e2b15

### bank

- Owns: src/quizkit/bank.py, tests/test_bank.py
- Depends on: src/quizkit/model.py
- Contract: src/quizkit/model.py
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k bank`
- Agent type: general-purpose
- Status: passed
- Outcome: built

### scoring

- Owns: src/quizkit/scoring.py, tests/test_scoring.py
- Depends on: src/quizkit/model.py
- Contract: src/quizkit/model.py
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k "responses or totals"`
- Agent type: general-purpose
- Status: passed
- Outcome: built

### Barrier

Scope: every changed file lies in one part's scope; model.py matches its hash. `python3 -m pytest -q tests/test_bank.py tests/test_scoring.py`: 11 passed. `python3 -m pytest -q tests/test_acceptance.py`: not run, as the acceptance tests import modules of later waves. No divergence; no retries.

## Wave 2

### stats

- Owns: src/quizkit/stats.py, tests/test_stats.py
- Depends on: src/quizkit/model.py, src/quizkit/scoring.py
- Contract: src/quizkit/model.py, `score` in src/quizkit/scoring.py
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k "difficulty or hardest or choice"`
- Agent type: general-purpose
- Status: pending
- Outcome:

### export

- Owns: src/quizkit/export.py, tests/test_export.py
- Depends on: src/quizkit/model.py, src/quizkit/scoring.py
- Contract: src/quizkit/model.py, `score` in src/quizkit/scoring.py
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k gradebook`
- Agent type: general-purpose
- Status: pending
- Outcome:

### Barrier

Not run yet.

## Wave 3

### cli

- Owns: src/quizkit/cli.py, tests/test_cli.py
- Depends on: bank, scoring, stats, export
- Contract: the README's Command section
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k cli`
- Agent type: general-purpose
- Status: pending
- Outcome:

### Barrier

Not run yet.

## Decided without asking

- Response letters are read in either case (`ac` is `AC`) -- the README does not say.

## Left for the user
""",
}

for name, text in FILES.items():
    target = pathlib.Path(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
