#!/bin/bash

echo "Setting up development environment..."

# Enable pnpm via corepack (ships with Node.js)
sudo corepack enable || echo "Warning: corepack enable failed; pnpm may not be available" >&2

# Installed here, not via the devcontainer feature: the feature installs as root,
# leaving @anthropic-ai unwritable so auto-update fails forever. Must precede
# codebase-memory-mcp, which registers its MCP server only if claude is present.
echo "Installing Claude Code CLI..."
claude_install_failed=0
# Retry once: a registry blip during create otherwise costs a rebuild.
npm install -g @anthropic-ai/claude-code \
    || npm install -g @anthropic-ai/claude-code \
    || claude_install_failed=1

# Install Node.js dependencies from all package.json files
echo "Installing Node.js dependencies..."
while IFS= read -r -d '' pkg_file; do
    dir=$(dirname "$pkg_file")
    echo "  Installing from $dir..."
    (cd "$dir" && CI=true pnpm install) || echo "Warning: pnpm install failed in $dir" >&2
done < <(find . -name "package.json" -not -path "*/node_modules/*" -not -path "*/.pnpm-store/*" -type f -print0)

# Install Python dependencies from all requirements.txt files
echo "Installing Python dependencies..."
while IFS= read -r -d '' req_file; do
    echo "  Installing from $req_file..."
    pip install -r "$req_file" || echo "Warning: pip install failed for $req_file" >&2
done < <(find . -name "requirements.txt" -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/.tox/*" -type f -print0)

# Install Python dependencies from all pyproject.toml files (editable installs)
echo "Installing Python editable packages..."
while IFS= read -r -d '' pyproject_file; do
    dir=$(dirname "$pyproject_file")
    echo "  Installing from $dir..."
    pip install -e "${dir}[dev]" || echo "Warning: pip install failed for $dir" >&2
done < <(find . -name "pyproject.toml" -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/.tox/*" -type f -print0)

# Delegated to `make install` so the install+wire steps live in one place.
# Grimoire has no pyproject.toml, so nothing above brings pre-commit in -- the
# loops over requirements.txt/pyproject.toml find no files here. The hooks it
# wires include two docker hooks, which need the daemon up; post-start.sh fixes
# the socket permissions.
if [ -f .pre-commit-config.yaml ]; then
    echo "Installing pre-commit and wiring the git hook..."
    make install || echo "Warning: 'make install' failed; run it by hand to enable the pre-commit hook" >&2
fi

# vscode-user-specific setup (volume mounts, ownership fixes)
if [ "$(whoami)" = "vscode" ]; then
    if [ -d "$HOME/.claude" ]; then
        # Fix ownership on Claude volume mount (fresh volumes are root-owned)
        sudo chown -R vscode:vscode "$HOME/.claude" || echo "Warning: could not fix ownership on $HOME/.claude" >&2

        # Persist ~/.claude.json across rebuilds by symlinking into the volume
        if [ ! -f "$HOME/.claude/claude.json" ]; then
            if [ -f "$HOME/.claude.json" ]; then
                cp "$HOME/.claude.json" "$HOME/.claude/claude.json" || echo "Warning: could not copy .claude.json to volume" >&2
            else
                echo '{}' > "$HOME/.claude/claude.json" || echo "Warning: could not create claude.json stub" >&2
            fi
        fi
        if [ -f "$HOME/.claude/claude.json" ]; then
            ln -sf "$HOME/.claude/claude.json" "$HOME/.claude.json" || echo "Warning: could not create claude.json symlink; config will not persist across rebuilds" >&2
        else
            echo "Warning: claude.json not created; config will not persist across rebuilds" >&2
        fi
    else
        echo "Warning: $HOME/.claude not found; config will not persist across rebuilds" >&2
    fi
fi

# Optional: Headroom token compression proxy (https://github.com/chopratejas/headroom)
# Reduces token usage 60-95% by compressing context sent to the LLM.
# Uncomment to enable:
# pip install "headroom-ai[proxy]"
# headroom init claude

# Install codebase-memory-mcp (structural code graph for Claude Code)
if ! command -v codebase-memory-mcp &>/dev/null; then
    echo "Installing codebase-memory-mcp..."
    (set -o pipefail; curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash -s -- --ui) || echo "Warning: codebase-memory-mcp install failed" >&2
fi

# Enable codebase-memory-mcp auto-indexing (indexes each project on first MCP
# session and re-indexes in the background on git changes). Guarded because the
# install above is best-effort; idempotent, so it re-applies on every rebuild.
if command -v codebase-memory-mcp &>/dev/null; then
    codebase-memory-mcp config set auto_index true || echo "Warning: could not enable codebase-memory-mcp auto_index" >&2
fi

gh auth status 2>/dev/null || echo "Warning: gh not authenticated. Run 'gh auth login' to enable GitHub CLI." >&2

# Reported here, at the end, so it survives the dependency-install output above
# rather than scrolling away. Not fatal: a non-zero postCreateCommand makes the
# spec skip postStart and postAttach, losing the Docker socket fix and the
# Codespaces path override.
if [ "$claude_install_failed" = 1 ]; then
    echo "ERROR: Claude Code CLI install failed. Run 'npm install -g @anthropic-ai/claude-code' to retry." >&2
fi

echo "Development environment setup complete!"
