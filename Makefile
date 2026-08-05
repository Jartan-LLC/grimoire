# Task runner for the local dev loop. Run `make` or `make help` to list targets.
# Grimoire has no build system -- these targets are the checks, nothing else.
# CI calls `make verify` directly, so this file is the single source for the
# Verify block rather than a copy of it.
#
# Recipes run under /bin/sh (dash on Debian and on the CI runners), so no
# bashisms. `$$` escapes a shell variable from Make's own expansion.

.PHONY: help install lint verify

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-10s %s\n", $$1, $$2}'

install:  ## Install pre-commit and wire the git hook
	pip install --quiet pre-commit
	# Skip hook wiring outside a git checkout; real failures still surface.
	if git rev-parse --git-dir >/dev/null 2>&1; then pre-commit install; fi

lint:  ## Lint all files via pre-commit (codespell, shellcheck, markdownlint, lychee, actionlint, zizmor, hygiene)
	pre-commit run --all-files

# `git grep -l` exits 0 on a match, 1 on none, and something else when the
# invocation itself failed -- a PCRE build without -P, a bad repo state.
# Treating every non-zero as "clean" would turn the ASCII gate into a silent
# no-op, so each case is handled on its own. The whole block is one logical
# line because Make runs each recipe line in a separate shell.
verify:  ## Run the correctness gate (ASCII, JSON parses, Codex drift)
	@echo "Checking for non-ASCII characters..."
	@set +e; git grep -lP '[^\x00-\x7F]'; rc=$$?; set -e; \
	case "$$rc" in \
	  0) echo "ERROR: non-ASCII characters found in the files listed above"; exit 1 ;; \
	  1) ;; \
	  *) echo "ERROR: git grep failed with exit $$rc"; exit 1 ;; \
	esac
	@echo "Checking that every tracked JSON file parses..."
	@python3 -c "import json,subprocess; [json.load(open(f)) for f in subprocess.run(['git','ls-files','*.json'],capture_output=True,text=True).stdout.split()]"
	@echo "Checking generated Codex files against their sources..."
	@python3 scripts/generate-codex.py --check
