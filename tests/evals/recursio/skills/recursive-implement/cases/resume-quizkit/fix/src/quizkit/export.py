"""The gradebook as CSV."""

from quizkit.model import Question, Response
from quizkit.scoring import score


def gradebook_csv(bank: list[Question], responses: list[Response]) -> str:
    """One row per student: points per question, blank where unanswered, then the total."""
    questions = {q.id: q for q in bank}
    cells: dict[str, dict[str, int]] = {}
    for response in responses:
        row = cells.setdefault(response.student, {})
        if response.chosen:
            row[response.question] = score(questions[response.question], response)
    lines = [",".join(["student", *questions, "total"])]
    for student in sorted(cells):
        row = cells[student]
        lines.append(",".join([student, *(str(row.get(q, "")) for q in questions), str(sum(row.values()))]))
    return "".join(line + "\n" for line in lines)
