"""The snap command line."""

USAGE = """\
snap take             take a snapshot of the current directory
snap list             list snapshots, newest first
snap prune --keep N   delete all but the newest N snapshots
snap prune --all      delete every snapshot, the latest included; this cannot be undone
"""
