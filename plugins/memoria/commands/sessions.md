# Sessions Command

Manage Claude Code session history - list, load, alias, and edit sessions stored in `~/.claude/sessions/`.

## Usage

`/sessions [list|load|alias|info|help] [options]`

## Actions

### List Sessions

Display all sessions with metadata, filtering, and pagination.

```bash
/sessions                              # List all sessions (default)
/sessions list                         # Same as above
/sessions list --limit 10              # Show 10 sessions
/sessions list --date 2026-02-01       # Filter by date
/sessions list --search abc            # Search by session ID
```

**Script:**
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/commands/sessions-cli.js" list
```

### Load Session

Load and display a session's content (by ID or alias).

```bash
/sessions load <id|alias>             # Load session
/sessions load 2026-02-01             # By date (for no-id sessions)
/sessions load a1b2c3d4               # By short ID
/sessions load my-alias               # By alias name
```

**Script:**
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/commands/sessions-cli.js" load $ARGUMENTS
```

### Create Alias

Create a memorable alias for a session.

```bash
/sessions alias <id> <name>           # Create alias
/sessions alias 2026-02-01 today-work # Create alias named "today-work"
```

**Script:**
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/commands/sessions-cli.js" alias $ARGUMENTS
```

### Remove Alias

Delete an existing alias.

```bash
/sessions alias --remove <name>        # Remove alias
/sessions unalias <name>               # Same as above
```

**Script:**
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/commands/sessions-cli.js" unalias $ARGUMENTS
```

### Session Info

Show detailed information about a session.

```bash
/sessions info <id|alias>              # Show session details
```

**Script:**
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/commands/sessions-cli.js" info $ARGUMENTS
```

### List Aliases

Show all session aliases.

```bash
/sessions aliases                      # List all aliases
```

**Script:**
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/commands/sessions-cli.js" aliases
```

## Arguments

$ARGUMENTS:
- `list [options]` - List sessions
  - `--limit <n>` - Max sessions to show (default: 50)
  - `--date <YYYY-MM-DD>` - Filter by date
  - `--search <pattern>` - Search in session ID
- `load <id|alias>` - Load session content
- `alias <id> <name>` - Create alias for session
- `alias --remove <name>` - Remove alias
- `unalias <name>` - Same as `--remove`
- `info <id|alias>` - Show session statistics
- `aliases` - List all aliases
- `help` - Show this help

## Examples

```bash
# List all sessions
/sessions list

# Create an alias for today's session
/sessions alias 2026-02-01 today

# Load session by alias
/sessions load today

# Show session info
/sessions info today

# Remove alias
/sessions alias --remove today

# List all aliases
/sessions aliases
```

## Notes

- Sessions are stored as markdown files in `~/.claude/sessions/`
- Aliases are stored in `~/.claude/session-aliases.json`
- Session IDs can be shortened (first 4-8 characters usually unique enough)
- Use aliases for frequently referenced sessions
