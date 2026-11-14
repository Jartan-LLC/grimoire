# Rotate a log

`logrot app.log --max-size 10M` rotates `app.log` once it passes 10 MB, renaming it to `app.log.1`.
`--keep N` sets how many old files stay; the default is 7.
