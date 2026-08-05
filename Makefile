# CI calls these targets directly, so this file is the single definition of the
# checks. Recipes run under dash both here and on the runners -- no bashisms.

.PHONY: help install lint verify

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

install:  ## Install pre-commit and wire the git hook
	pip install --quiet pre-commit
	# Skip hook wiring outside a git checkout; real failures still surface.
	if git rev-parse --git-dir >/dev/null 2>&1; then pre-commit install; fi

lint:  ## Lint all files via pre-commit (codespell, shellcheck, markdownlint, lychee, actionlint, zizmor, hygiene)
	pre-commit run --all-files

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
	@python3 -c "import json,subprocess; [json.load(open(f)) for f in subprocess.run(['git','ls-files','*.json'],capture_output=True,text=True).stdout.split()]"
	@echo "Checking generated Codex files against their sources..."
	@python3 scripts/generate-codex.py --check
