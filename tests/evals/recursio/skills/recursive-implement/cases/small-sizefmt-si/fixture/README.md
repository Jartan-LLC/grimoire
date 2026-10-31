# sizefmt

Prints byte counts the way people read them: `sizefmt 1536` prints `1.5 KiB`. TypeScript that Node 24 or later runs directly, with no dependencies.

```console
$ sizefmt 512 1536 3221225472
512 B
1.5 KiB
3.0 GiB
```

Sizes below 1024 print as whole bytes; larger ones are divided by 1024 until they are below it, up to TiB.

## Options

- `--precision N`: decimals to print, 1 by default.

A size that is not a whole number of bytes, or a bad option, prints a message to stderr and exits 2.
