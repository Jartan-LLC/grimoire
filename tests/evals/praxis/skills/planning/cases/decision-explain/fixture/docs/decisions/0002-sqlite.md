# 2. Store data in SQLite

Status: accepted, 2025-04-02.

## Context

The app runs on one small server and has one writer: the nightly import. Reads are a few
hundred a day.

## Decision

Use SQLite, in WAL mode, with the file on the server's disk.

## Consequences

No database server to run or back up separately; the file is backed up with the disk. If a
second writer appears, revisit.
