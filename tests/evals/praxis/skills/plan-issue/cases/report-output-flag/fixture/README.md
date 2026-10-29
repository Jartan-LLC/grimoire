# sizecheck

```bash
sizecheck dist/                 # table of gzipped sizes
sizecheck dist/ --budget 50kb   # exit 1 when a file is over 50 kB gzipped
sizecheck dist/ --json          # the same report as JSON
sizecheck dist/ -o              # also write an HTML report and open it in the browser
```

| Flag | Short | Meaning |
| --- | --- | --- |
| `--budget <size>` | `-b` | largest gzipped size allowed per file |
| `--json` | | print JSON instead of the table |
| `--open` | `-o` | write `sizecheck-report.html` and open it |
