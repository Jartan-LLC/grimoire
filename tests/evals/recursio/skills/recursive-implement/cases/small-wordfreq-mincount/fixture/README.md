# wordfreq

Counts the words of a text file and prints them most frequent first, one `count word` line each. Words are runs of letters and apostrophes, compared in lower case; ties print in alphabetical order.

## Usage

```console
$ wordfreq notes.txt
3 the
2 and
1 cat
```

- `wordfreq FILE`: every word of FILE with its count.
- `--top N`: only the N most frequent words.

A missing file or a bad option prints a message to stderr and exits 2.
