# rewrap

```bash
rewrap --width 72 < notes.txt
```

Reads text on stdin and prints it wrapped at spaces to at most `--width` characters a line
(72 by default). A word longer than the width keeps a line of its own.
