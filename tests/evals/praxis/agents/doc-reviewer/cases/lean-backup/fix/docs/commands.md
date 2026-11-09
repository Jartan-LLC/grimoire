# Commands

## vault init

Run `vault init` in a directory to make it a vault. It writes `.vault/` beside your files.

## vault status

`vault status` lists the files added, changed or removed since the last backup.

## vault backup

`vault backup DEST` writes a dated `.tar.gz` archive of the vault into `DEST`. It needs GNU or
BusyBox tar. If tar reports an error, the backup fails; fix the cause and run it again.

## vault restore

`vault restore ARCHIVE` unpacks `ARCHIVE` into the vault. Without `ARCHIVE` it restores the newest
archive in `DEST`.
