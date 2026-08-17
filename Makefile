# CI calls these targets directly, so this file is the single definition of the
# checks. Recipes run under dash both here and on the runners -- no bashisms.

.PHONY: help install lint verify test

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

install:  ## Install pre-commit and wire the git hook
	pip install --quiet -r ci/requirements.txt
	# Skip hook wiring outside a git checkout; real failures still surface.
	if git rev-parse --git-dir >/dev/null 2>&1; then pre-commit install; fi

lint:  ## Lint all files via pre-commit (codespell, shellcheck, markdownlint, lychee, actionlint, zizmor, hygiene)
	pre-commit run --all-files --show-diff-on-failure

# `git grep -l` exits 1 on no match, so `|| true` would turn the ASCII gate into
# a permanent no-op and any other non-zero means the invocation itself failed.
# One logical line because Make gives each recipe line its own shell.
verify:  ## Run the correctness gate (ASCII, JSON parses, Codex drift)
	@echo "Checking for non-ASCII characters..."
	@set +e; git grep -lP '[^\x00-\x7F]'; rc=$$?; set -e; \
	case "$$rc" in \
	  0) echo "ERROR: non-ASCII characters found in the files listed above"; exit 1 ;; \
	  1) ;; \
	  *) echo "ERROR: git grep failed with exit $$rc"; exit 1 ;; \
	esac
	@echo "Checking that every tracked JSON file parses..."
	@python3 -c "import json,subprocess; files=subprocess.run(['git','ls-files','*.json'],capture_output=True,text=True,check=True).stdout.split(); assert files, 'git ls-files matched no JSON -- gate would pass having checked nothing'; [json.load(open(f)) for f in files]"
	@echo "Checking generated Codex files against their sources..."
	@python3 scripts/generate-codex.py --check

# Each half hands its runner an explicit file list from `git ls-files`, and
# asserts the list is non-empty for the same reason the JSON check above does:
# `git ls-files` exits 0 on no match and `node --test` with no arguments walks
# the whole tree instead of failing, so an unguarded list is a silent pass.
# Why a list rather than a directory or a glob: see CONTRIBUTING.md.
#
# Node runs first, and Make stops at the first failing line, so a Node failure
# hides the Python result -- the same trade `verify` makes above.
test:  ## Run the unit tests and hook process contracts (Node, then Python)
	@echo "Running the Node tests..."
	@files=$$(git ls-files 'tests/*.test.js'); \
	if [ -z "$$files" ]; then echo "ERROR: git ls-files matched no Node tests -- gate would pass having checked nothing"; exit 1; fi; \
	node --test $$files
	@echo "Running the Python tests..."
	@files=$$(git ls-files 'tests/test_*.py' 'tests/*/test_*.py'); \
	if [ -z "$$files" ]; then echo "ERROR: git ls-files matched no Python tests -- gate would pass having checked nothing"; exit 1; fi; \
	python3 -m unittest $$files
