# Rotate a log

`logrot app.log --max-size 10M` rotates `app.log` once it passes 10 MB, renaming it to `app.log.1`.
`--keep N` sets how many old files stay; the default is 7.

An empty log is left as it is, not rotated. On NFS, a rename is not atomic. A named pipe given
as FILE is left alone.
