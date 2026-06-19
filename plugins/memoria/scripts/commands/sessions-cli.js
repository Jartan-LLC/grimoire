#!/usr/bin/env node

const path = require('path');
const sm = require(path.join(__dirname, '..', 'lib', 'session-manager'));
const aa = require(path.join(__dirname, '..', 'lib', 'session-aliases'));

const args = process.argv.slice(2);
const action = (args[0] || 'list').toLowerCase();

function listSessions() {
  const result = sm.getAllSessions({ limit: 20 });
  const aliases = aa.listAliases();
  const aliasMap = {};
  for (const a of aliases) aliasMap[a.sessionPath] = a.name;

  console.log('Sessions (showing ' + result.sessions.length + ' of ' + result.total + '):');
  console.log('');
  console.log('ID        Date        Time     Size     Lines  Alias');
  console.log('────────────────────────────────────────────────────');

  for (const s of result.sessions) {
    const alias = aliasMap[s.filename] || '';
    const size = sm.getSessionSize(s.sessionPath);
    const stats = sm.getSessionStats(s.sessionPath);
    const id = s.shortId === 'no-id' ? '(none)' : s.shortId.slice(0, 8);
    const time = s.modifiedTime.toTimeString().slice(0, 5);

    console.log(id.padEnd(8) + ' ' + s.date + '  ' + time + '   ' + size.padEnd(7) + '  ' + String(stats.lineCount).padEnd(5) + '  ' + alias);
  }
}

function loadSession(id) {
  if (!id) {
    console.log('Usage: /sessions load <id|alias>');
    process.exit(1);
  }

  const resolved = aa.resolveAlias(id);
  const sessionId = resolved ? resolved.sessionPath : id;

  const session = sm.getSessionById(sessionId, true);
  if (!session) {
    console.log('Session not found: ' + id);
    process.exit(1);
  }

  const stats = sm.getSessionStats(session.sessionPath);
  const size = sm.getSessionSize(session.sessionPath);
  const aliases = aa.getAliasesForSession(session.filename);

  console.log('Session: ' + session.filename);
  console.log('Path: ~/.claude/sessions/' + session.filename);
  console.log('');
  console.log('Statistics:');
  console.log('  Lines: ' + stats.lineCount);
  console.log('  Total items: ' + stats.totalItems);
  console.log('  Completed: ' + stats.completedItems);
  console.log('  In progress: ' + stats.inProgressItems);
  console.log('  Size: ' + size);
  console.log('');

  if (aliases.length > 0) {
    console.log('Aliases: ' + aliases.map(a => a.name).join(', '));
    console.log('');
  }

  if (session.metadata.title) {
    console.log('Title: ' + session.metadata.title);
    console.log('');
  }

  if (session.metadata.started) {
    console.log('Started: ' + session.metadata.started);
  }

  if (session.metadata.lastUpdated) {
    console.log('Last Updated: ' + session.metadata.lastUpdated);
  }
}

function createAlias(sessionId, aliasName) {
  if (!sessionId || !aliasName) {
    console.log('Usage: /sessions alias <id> <name>');
    process.exit(1);
  }

  const session = sm.getSessionById(sessionId);
  if (!session) {
    console.log('Session not found: ' + sessionId);
    process.exit(1);
  }

  const result = aa.setAlias(aliasName, session.filename);
  if (result.success) {
    console.log('✓ Alias created: ' + aliasName + ' → ' + session.filename);
  } else {
    console.log('✗ Error: ' + result.error);
    process.exit(1);
  }
}

function removeAlias(aliasName) {
  if (!aliasName) {
    console.log('Usage: /sessions alias --remove <name>');
    process.exit(1);
  }

  const result = aa.deleteAlias(aliasName);
  if (result.success) {
    console.log('✓ Alias removed: ' + aliasName);
  } else {
    console.log('✗ Error: ' + result.error);
    process.exit(1);
  }
}

function showInfo(id) {
  if (!id) {
    console.log('Usage: /sessions info <id|alias>');
    process.exit(1);
  }

  const resolved = aa.resolveAlias(id);
  const sessionId = resolved ? resolved.sessionPath : id;

  const session = sm.getSessionById(sessionId, true);
  if (!session) {
    console.log('Session not found: ' + id);
    process.exit(1);
  }

  const stats = sm.getSessionStats(session.sessionPath);
  const size = sm.getSessionSize(session.sessionPath);
  const aliases = aa.getAliasesForSession(session.filename);

  console.log('Session Information');
  console.log('════════════════════');
  console.log('ID:          ' + (session.shortId === 'no-id' ? '(none)' : session.shortId));
  console.log('Filename:    ' + session.filename);
  console.log('Date:        ' + session.date);
  console.log('Modified:    ' + session.modifiedTime.toISOString().slice(0, 19).replace('T', ' '));
  console.log('');
  console.log('Content:');
  console.log('  Lines:         ' + stats.lineCount);
  console.log('  Total items:   ' + stats.totalItems);
  console.log('  Completed:     ' + stats.completedItems);
  console.log('  In progress:   ' + stats.inProgressItems);
  console.log('  Size:          ' + size);
  if (aliases.length > 0) {
    console.log('Aliases:     ' + aliases.map(a => a.name).join(', '));
  }
}

function listAliases() {
  const aliases = aa.listAliases();
  console.log('Session Aliases (' + aliases.length + '):');
  console.log('');

  if (aliases.length === 0) {
    console.log('No aliases found.');
  } else {
    console.log('Name          Session File                    Title');
    console.log('─────────────────────────────────────────────────────────────');
    for (const a of aliases) {
      const name = a.name.padEnd(12);
      const file = (a.sessionPath.length > 30 ? a.sessionPath.slice(0, 27) + '...' : a.sessionPath).padEnd(30);
      const title = a.title || '';
      console.log(name + ' ' + file + ' ' + title);
    }
  }
}

switch (action) {
  case 'list':
    listSessions();
    break;
  case 'load':
    loadSession(args[1]);
    break;
  case 'alias':
    if (args[1] === '--remove') {
      removeAlias(args[2]);
    } else {
      createAlias(args[1], args[2]);
    }
    break;
  case 'unalias':
    removeAlias(args[1]);
    break;
  case 'info':
    showInfo(args[1]);
    break;
  case 'aliases':
    listAliases();
    break;
  case 'help':
    console.log('Usage: /sessions [list|load|alias|unalias|info|aliases|help]');
    console.log('');
    console.log('  list                  List all sessions');
    console.log('  load <id|alias>       Load session content');
    console.log('  alias <id> <name>     Create alias for session');
    console.log('  alias --remove <name> Remove alias');
    console.log('  unalias <name>        Remove alias');
    console.log('  info <id|alias>       Show session details');
    console.log('  aliases               List all aliases');
    console.log('  help                  Show this help');
    break;
  default:
    console.log('Unknown action: ' + action);
    console.log('Run /sessions help for usage.');
    process.exit(1);
}
