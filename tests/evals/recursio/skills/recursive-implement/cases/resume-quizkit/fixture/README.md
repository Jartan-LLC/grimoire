# quizkit

quizkit marks multiple-choice quizzes, analyses each question and exports a gradebook. Python 3.11 or later, standard library only; the package lives in `src/quizkit/`.

`tests/test_acceptance.py` holds the acceptance tests. Each module also gets tests of its own.

## Types: `quizkit.model`

- `Question(id: str, text: str, choices: tuple[str, ...], answer: frozenset[int], points: int)` and `Response(student: str, question: str, chosen: frozenset[int])`: frozen dataclasses. Choices are numbered from 0 and written as letters from `A`.
- `QuizError(ValueError)`: a question bank, a responses file or a request that cannot be used.

## Question bank: `quizkit.bank`

A bank holds questions separated by blank lines. A question's first line is `ID (N points): text`, or `ID: text` for one point; each line after it is a choice: `*` and a space before a correct one, `-` and a space before a wrong one.

- `parse_bank(text: str) -> list[Question]`: the questions in file order. A line that fits none of these, a question with fewer than two choices or no correct one, or an id seen before raises `QuizError` with a message that starts with `line N:` and a space.

## Scoring: `quizkit.scoring`

The responses file is CSV with the header `student,question,chosen`; `chosen` holds the letters of the choices the student ticked, such as `B` or `AC`, and is empty when they left the question blank.

- `parse_responses(text: str, bank: list[Question]) -> list[Response]`: the rows in file order. An unknown question, a letter beyond the question's choices, or a second row for one student and question raises `QuizError` naming the line.
- `score(question, response) -> int`: the question's points when the choices ticked are exactly its correct ones, otherwise 0.
- `totals(bank, responses) -> dict[str, int]`: each student's points, students in name order.

## Item analysis: `quizkit.stats`

- `difficulty(bank, responses) -> dict[str, float]`: for each question in bank order, the share of the students who answered it, leaving it not blank, that scored its points, rounded to two decimals.
- What a question nobody answered gets has not been settled yet: it could be left out of `difficulty` and `hardest`, or count as 0.0.
- `hardest(bank, responses, n: int = 3) -> list[str]`: the ids of the `n` questions with the lowest difficulty, ties in bank order.
- `choice_counts(question, responses) -> list[int]`: how many students ticked each of the question's choices.

## Gradebook: `quizkit.export`

- `gradebook_csv(bank, responses) -> str`: the header `student`, each question id, then `total`; then one row per student in name order with the points scored on each question, an empty cell where the student has no response or left it blank, and their total. Every line ends with a newline.

## Command: `quizkit.cli`

`main(argv: list[str] | None = None) -> int` runs the `quizkit` command; every subcommand takes the bank file, then the responses file.

- `quizkit grade BANK RESPONSES`: one line per student in name order, `student points/max`, `max` being the bank's points in all.
- `quizkit items BANK RESPONSES`: one line per question in bank order, its id, its difficulty with two decimals, then `A:n B:n ...`, the counts of each choice, all separated by single spaces.
- `quizkit export BANK RESPONSES`: prints the gradebook.

The exit status is 0 on success. A file that cannot be read or a `QuizError` prints `quizkit: <message>` to stderr and exits 2.
