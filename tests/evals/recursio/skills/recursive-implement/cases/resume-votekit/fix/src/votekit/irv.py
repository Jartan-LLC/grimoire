# SPDX-License-Identifier: MIT
"""Count ballots by instant runoff."""

from votekit.model import Ballot, Result, Round


def instant_runoff(ballots: list[Ballot], candidates: list[str]) -> Result:
    left = list(candidates)
    rounds: list[Round] = []
    while left:
        counts = dict.fromkeys(left, 0)
        for ballot in ballots:
            choice = next((name for name in ballot.ranking if name in counts), None)
            if choice is not None:
                counts[choice] += 1
        counted = sum(counts.values())
        leader = max(counts, key=lambda name: counts[name])
        if counts[leader] * 2 > counted:
            rounds.append(Round(counts, None))
            return Result(leader, rounds)
        fewest = min(counts.values())
        tied = [name for name in left if counts[name] == fewest]
        if len(tied) == len(left):
            rounds.append(Round(counts, None))
            return Result(None, rounds)
        out = min(tied, key=lambda name: (rounds[0].counts[name] if rounds else counts[name], name))
        rounds.append(Round(counts, out))
        left.remove(out)
    return Result(None, rounds)
