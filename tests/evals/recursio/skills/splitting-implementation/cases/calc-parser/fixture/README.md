# calc

Evaluates arithmetic expressions: `+ - * / ^`, unary minus, parentheses, numbers such as `3`,
`2.5` and `1e3`, and variables passed in a dict (`evaluate("2 * x ^ 2", {"x": 3})` is 18).
A syntax error raises `calc.CalcSyntaxError` with the column it was found at.
