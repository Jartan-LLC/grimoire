# SPDX-License-Identifier: MIT
"""The votekit command."""

import argparse
import sys

from votekit.ballots import parse_ballots
from votekit.irv import instant_runoff
from votekit.model import BallotError
from votekit.plurality import plurality
from votekit.render import render_json, render_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="votekit")
    commands = parser.add_subparsers(dest="command", required=True)
    count = commands.add_parser("count")
    count.add_argument("file")
    count.add_argument("--candidates", required=True)
    count.add_argument("--method", choices=["irv", "plurality"], default="irv")
    count.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    names = args.candidates.split(",")
    try:
        with open(args.file) as handle:
            ballots = parse_ballots(handle.read(), names)
    except (OSError, BallotError) as error:
        print(f"votekit: {error}", file=sys.stderr)
        return 2
    result = (instant_runoff if args.method == "irv" else plurality)(ballots, names)
    print(render_json(result) if args.json else render_text(result), end="" if not args.json else "\n")
    return 0 if result.winner else 1
