"""Invoice totals."""


def sum_lines(lines):
    tmp = 0
    for line in lines:
        tmp += line["qty"] * line["price"]
    return tmp
