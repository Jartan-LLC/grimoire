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

An archive written while the clock ran ahead counts as the newest. A `.part` file that a kill or a
power cut left over a day before is removed at the next backup. If a file shrinks while tar reads
it, tar pads it with zeros, so the backup fails. Restore sets the directory's mode and modification
time from the archive, as GNU tar does.
