# tempconv

Converts a temperature from one unit to another and prints it with one decimal. Perl 5.36 or later, core modules only; the code lives in `lib/Tempconv.pm` and the command in `bin/tempconv`.

## Usage

```console
$ tempconv --from C --to F 21.5
70.7
```

- `--from UNIT`: the unit of the value given, `C` (Celsius) or `F` (Fahrenheit).
- `--to UNIT`: the unit to print it in, `C` or `F`.

An unknown unit, a missing option or a value that is not a number prints `tempconv: <message>` to stderr and exits 2.
