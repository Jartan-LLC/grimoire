# votekit

votekit counts ranked ballots, by plurality or by instant runoff, and reports the result. Python 3.11 or later, standard library only; the package lives in `src/votekit/`.

`tests/test_acceptance.py` holds the acceptance tests. Each module also gets tests of its own.

## Types: `votekit.model`

- `Ballot(voter: str, ranking: tuple[str, ...])`, `Round(counts: dict[str, int], eliminated: str | None)` and `Result(winner: str | None, rounds: list[Round])`: frozen dataclasses.
- `BallotError(ValueError)`: a ballot file that cannot be read.

## Ballots: `votekit.ballots`

A ballot file holds one ballot per line, `voter: A > B > C`, ranking candidates from most to least preferred. Blank lines and lines starting with `#` are skipped.

- `parse_ballots(text: str, candidates: list[str]) -> list[Ballot]`: the ballots in file order. A ballot may rank only some candidates, or none. A line without `:` or a voter, a candidate not in `candidates`, a candidate ranked twice or a voter seen before raises `BallotError` with a message that starts with `line N:` and a space.

## Plurality: `votekit.plurality`

- `plurality(ballots, candidates) -> Result`: one round counting first choices, every candidate in `counts`. The candidate with the most wins; a tie for the most, or no first choices at all, leaves `winner` as None.

## Instant runoff: `votekit.irv`

- `instant_runoff(ballots, candidates) -> Result`: each round counts every ballot for its highest-ranked candidate still in the race; a ballot with none left is exhausted and not counted. A candidate with more than half of the counted ballots wins. Otherwise the candidate with the fewest votes is eliminated and the next round runs. Each round's `counts` holds every candidate still in the race, zeros included, and `eliminated` names the candidate it removed, or is None in the last round. When the candidates left all have the same number of votes, the race ends with no winner.
- How to break a tie for the fewest votes between some of the candidates has not been settled yet: eliminating every tied candidate at once and eliminating the one with fewer first-round votes are both on the table.

## Rendering: `votekit.render`

- `render_text(result) -> str`: one line per round, `Round N: A 4, B 3, C 2`, candidates by votes, most first, then by name, followed by a space and `-- C out` when the round eliminated one; then `Winner: A`, or `No winner`. Every line ends with a newline.
- `render_json(result) -> str`: `{"winner": ..., "rounds": [{"counts": {...}, "eliminated": ...}, ...]}`, with the keys in that order.

## Command: `votekit.cli`

`main(argv: list[str] | None = None) -> int` runs `votekit count FILE --candidates A,B,C [--method irv|plurality] [--json]`: it reads the ballots, counts them by instant runoff (the default) or by plurality, and prints the text rendering, or the JSON one with `--json`. It exits 0 when there is a winner and 1 when there is none. An unreadable file or a `BallotError` prints `votekit: <message>` to stderr and exits 2.
