"""The quizkit command."""

import argparse
import string
import sys
from pathlib import Path

from quizkit.bank import parse_bank
from quizkit.export import gradebook_csv
from quizkit.model import QuizError
from quizkit.scoring import parse_responses, totals
from quizkit.stats import choice_counts, difficulty


def main(argv: list[str] | None = None) -> int:
    """Run the quizkit command; return its exit status."""
    parser = argparse.ArgumentParser(prog="quizkit")
    parser.add_argument("command", choices=["grade", "items", "export"])
    parser.add_argument("bank")
    parser.add_argument("responses")
    args = parser.parse_args(argv)
    try:
        bank = parse_bank(Path(args.bank).read_text())
        responses = parse_responses(Path(args.responses).read_text(), bank)
    except (OSError, QuizError) as error:
        print(f"quizkit: {error}", file=sys.stderr)
        return 2
    if args.command == "grade":
        most = sum(q.points for q in bank)
        for student, points in totals(bank, responses).items():
            print(f"{student} {points}/{most}")
    elif args.command == "items":
        shares = difficulty(bank, responses)
        for question in bank:
            counts = " ".join(f"{string.ascii_uppercase[i]}:{n}" for i, n in enumerate(choice_counts(question, responses)))
            print(f"{question.id} {shares.get(question.id, 0.0):.2f} {counts}")
    else:
        sys.stdout.write(gradebook_csv(bank, responses))
    return 0
