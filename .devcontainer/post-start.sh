#!/bin/bash

# Fix Docker socket permissions (docker-outside-of-docker feature)
sudo chmod 666 /var/run/docker-host.sock 2>/dev/null || true

# Claude Code is installed by post-create, which does not re-run on start or
# attach -- so a registry blip during create would otherwise cost a rebuild.
# Best-effort like everything else here: a failure must not fail postStart.
if command -v npm &>/dev/null && ! command -v claude &>/dev/null; then
    echo "Claude Code CLI missing; retrying install..."
    npm install -g @anthropic-ai/claude-code \
        || echo "Warning: Claude Code CLI install failed" >&2
fi

# In GitHub Codespaces, HOST_PROJECT_PATH (set via containerEnv) resolves to the
# host-side path, which is meaningless inside the container. Override it with the
# container workspace path so downstream Docker bind-mounts work correctly.
if [ "$CODESPACES" = "true" ]; then
    # Login shells (SSH)
    echo "export HOST_PROJECT_PATH=\"$CONTAINER_WORKSPACE_FOLDER\"" | sudo tee /etc/profile.d/codespaces-host-path.sh >/dev/null
    # Interactive non-login shells (VS Code integrated terminals)
    grep -q 'HOST_PROJECT_PATH=.*Codespaces' ~/.bashrc 2>/dev/null || \
        echo "export HOST_PROJECT_PATH=\"$CONTAINER_WORKSPACE_FOLDER\"  # Codespaces override" >> ~/.bashrc
    # Non-interactive bash (Claude Code CLI, VS Code tasks) -- BASH_ENV tells bash
    # to source a file before executing scripts. We set it in both /etc/environment
    # (picked up by new PAM sessions) and ~/.bashrc (inherited by child processes).
    echo "export HOST_PROJECT_PATH=\"$CONTAINER_WORKSPACE_FOLDER\"" | sudo tee /etc/codespaces-env.sh >/dev/null
    grep -q 'BASH_ENV' ~/.bashrc 2>/dev/null || echo 'export BASH_ENV=/etc/codespaces-env.sh' >> ~/.bashrc
    grep -q 'BASH_ENV' /etc/environment 2>/dev/null || echo 'BASH_ENV=/etc/codespaces-env.sh' | sudo tee -a /etc/environment >/dev/null
fi
