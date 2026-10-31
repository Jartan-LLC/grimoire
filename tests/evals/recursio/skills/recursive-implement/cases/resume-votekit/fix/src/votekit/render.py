# SPDX-License-Identifier: MIT
"""Render a result as text or JSON."""

import json

from votekit.model import Result


def render_text(result: Result) -> str:
    lines = []
    for number, round_ in enumerate(result.rounds, start=1):
        ordered = sorted(round_.counts.items(), key=lambda item: (-item[1], item[0]))
        line = f"Round {number}: " + ", ".join(f"{name} {votes}" for name, votes in ordered)
        if round_.eliminated:
            line += f" -- {round_.eliminated} out"
        lines.append(line)
    lines.append(f"Winner: {result.winner}" if result.winner else "No winner")
    return "".join(f"{line}\n" for line in lines)


def render_json(result: Result) -> str:
    rounds = [{"counts": r.counts, "eliminated": r.eliminated} for r in result.rounds]
    return json.dumps({"winner": result.winner, "rounds": rounds})
