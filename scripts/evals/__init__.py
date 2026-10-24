"""Local skill evals: run a suite's cases headless against two plugin versions and compare.

`scripts/eval.py` is the entry point; `tests/evals/README.md` holds the method.
Everything that spends inference runs on the user's own `claude` login, never in CI.
"""
