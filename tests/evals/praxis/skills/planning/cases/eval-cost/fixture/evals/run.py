import argparse
import json
import pathlib

CASES = pathlib.Path(__file__).parent / "cases"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    args = ap.parse_args()
    cases = sorted(CASES.glob("*.json"))
    print(f"would run {len(cases)} cases x 5 on {args.model}")


main()
