# isbntool

Checks ISBNs. Python 3.11 or later, standard library only; the package lives in `src/isbntool/`.

## Usage

```console
$ isbntool check 0-306-40615-2 978-0-306-40615-8
0-306-40615-2 valid
978-0-306-40615-8 invalid
```

- `isbntool check ISBN...`: one line per ISBN, the ISBN as given and `valid` or `invalid`. Hyphens and spaces are ignored; an ISBN-10 may end in `X`.

The exit status is 1 when any ISBN is invalid, otherwise 0.
