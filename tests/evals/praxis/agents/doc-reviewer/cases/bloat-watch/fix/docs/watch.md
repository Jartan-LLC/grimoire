# Rebuild the index as you write

Run `notes watch ~/notes` in a terminal and leave it running. Each time you save a note, the
index is rebuilt. Stop it with Ctrl-C.

On Linux, a tree with more files than `fs.inotify.max_user_watches` falls back to polling. Editors
that save by renaming a temporary file, such as vim, are seen as a new file. On a network drive,
changes are polled every 5 seconds.
