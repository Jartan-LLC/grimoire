"""Acceptance tests for quizkit, as the README specifies."""

import pytest

from quizkit.bank import parse_bank
from quizkit.cli import main
from quizkit.export import gradebook_csv
from quizkit.model import QuizError, Question, Response
from quizkit.scoring import parse_responses, score, totals
from quizkit.stats import choice_counts, difficulty, hardest

BANK = """Q1 (2 points): Which of these are prime?
* 2
- 4
* 7

Q2: What is the capital of Peru?
- Quito
* Lima
- La Paz

Q3: Which planet is largest?
- Mars
* Jupiter
"""

RESPONSES = """student,question,chosen
cleo,Q1,AC
cleo,Q2,B
cleo,Q3,A
amir,Q1,A
amir,Q2,B
amir,Q3,B
bea,Q1,AC
bea,Q2,
bea,Q3,B
"""


def bank():
    return parse_bank(BANK)


def responses():
    return parse_responses(RESPONSES, bank())


def test_parse_bank():
    q1, q2, q3 = bank()
    assert q1 == Question("Q1", "Which of these are prime?", ("2", "4", "7"), frozenset({0, 2}), 2)
    assert (q2.points, q2.answer, q3.choices) == (1, frozenset({1}), ("Mars", "Jupiter"))


def test_a_question_without_a_correct_choice_names_its_line():
    with pytest.raises(QuizError, match=r"^line \d+: "):
        parse_bank("Q1: Pick one\n- a\n- b\n")


def test_responses_and_scores():
    rows = responses()
    assert rows[0] == Response("cleo", "Q1", frozenset({0, 2}))
    assert rows[7] == Response("bea", "Q2", frozenset())
    q1 = bank()[0]
    assert [score(q1, r) for r in rows if r.question == "Q1"] == [2, 0, 2]


def test_bad_response_names_its_line():
    with pytest.raises(QuizError, match="line 3"):
        parse_responses("student,question,chosen\ncleo,Q1,A\ncleo,Q3,C\n", bank())


def test_totals_in_name_order():
    assert list(totals(bank(), responses()).items()) == [("amir", 2), ("bea", 3), ("cleo", 3)]


def test_difficulty_counts_only_those_who_answered():
    assert difficulty(bank(), responses()) == {"Q1": 0.67, "Q2": 1.0, "Q3": 0.67}


def test_hardest_breaks_ties_in_bank_order():
    assert hardest(bank(), responses(), 2) == ["Q1", "Q3"]


def test_choice_counts():
    assert choice_counts(bank()[0], responses()) == [3, 0, 2]


def test_gradebook():
    assert gradebook_csv(bank(), responses()) == (
        "student,Q1,Q2,Q3,total\namir,0,1,1,2\nbea,2,,1,3\ncleo,2,1,0,3\n"
    )


@pytest.fixture
def files(tmp_path):
    (tmp_path / "bank.txt").write_text(BANK)
    (tmp_path / "responses.csv").write_text(RESPONSES)
    return str(tmp_path / "bank.txt"), str(tmp_path / "responses.csv")


def test_cli_grade(files, capsys):
    assert main(["grade", *files]) == 0
    assert capsys.readouterr().out == "amir 2/4\nbea 3/4\ncleo 3/4\n"


def test_cli_items(files, capsys):
    assert main(["items", *files]) == 0
    assert capsys.readouterr().out == "Q1 0.67 A:3 B:0 C:2\nQ2 1.00 A:0 B:2 C:0\nQ3 0.67 A:1 B:2\n"


def test_cli_export(files, capsys):
    assert main(["export", *files]) == 0
    assert capsys.readouterr().out.splitlines()[0] == "student,Q1,Q2,Q3,total"


def test_cli_bad_bank_exits_2(tmp_path, capsys):
    (tmp_path / "bank.txt").write_text("Q1: one\n* a\n")
    (tmp_path / "r.csv").write_text("student,question,chosen\n")
    assert main(["grade", str(tmp_path / "bank.txt"), str(tmp_path / "r.csv")]) == 2
    assert capsys.readouterr().err.startswith("quizkit: line ")
