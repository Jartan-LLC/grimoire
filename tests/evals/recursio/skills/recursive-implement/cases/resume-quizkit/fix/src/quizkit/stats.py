"""Item analysis: how hard each question was, and which choices were ticked."""

from quizkit.model import Question, Response
from quizkit.scoring import score


def difficulty(bank: list[Question], responses: list[Response]) -> dict[str, float]:
    """The share of those who answered each question that scored; unanswered questions are left out."""
    result: dict[str, float] = {}
    for question in bank:
        answered = [r for r in responses if r.question == question.id and r.chosen]
        if answered:
            right = sum(1 for r in answered if score(question, r))
            result[question.id] = round(right / len(answered), 2)
    return result


def hardest(bank: list[Question], responses: list[Response], n: int = 3) -> list[str]:
    """The ids of the n questions with the lowest difficulty, ties in bank order."""
    shares = difficulty(bank, responses)
    order = [q.id for q in bank if q.id in shares]
    return sorted(order, key=lambda qid: shares[qid])[:n]


def choice_counts(question: Question, responses: list[Response]) -> list[int]:
    """How many students ticked each choice."""
    counts = [0] * len(question.choices)
    for response in responses:
        if response.question == question.id:
            for index in response.chosen:
                counts[index] += 1
    return counts
