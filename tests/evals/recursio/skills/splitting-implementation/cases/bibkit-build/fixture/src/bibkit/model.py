"""The records the bibkit modules pass to one another."""

import enum
from dataclasses import dataclass, field

# Full month names, January first; BibTeX's jan..dec macros expand to these.
MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


class EntryType(enum.Enum):
    """The kind of work an entry describes, named as BibTeX names it."""

    ARTICLE = "article"
    BOOK = "book"
    INBOOK = "inbook"
    INCOLLECTION = "incollection"
    INPROCEEDINGS = "inproceedings"
    PHDTHESIS = "phdthesis"
    MASTERSTHESIS = "mastersthesis"
    TECHREPORT = "techreport"
    ONLINE = "online"
    MISC = "misc"


@dataclass(frozen=True)
class Name:
    """One person's name in BibTeX's four parts.

    `family` is the part a name is sorted and cited under. A lower-case particle before it goes
    in `von`, not in `family`: Johannes van der Waals is
    Name(family="Waals", given="Johannes", von="van der"). A suffix such as "Jr." or "III" goes
    in `jr`. A corporate author written in braces, such as {World Health Organization}, is all
    `family`, with the braces removed. The literal name "others" in an author list is kept as
    Name(family="others"), meaning more authors than are listed.
    """

    family: str
    given: str = ""
    von: str = ""
    jr: str = ""


@dataclass
class Entry:
    """One bibliography entry.

    `fields` maps lower-case field names to values with macros expanded, concatenations joined
    and the outer delimiters removed. Inner braces, which protect case, are kept:
    {"title": "The {NASA} missions"}. `fields` never holds "author" or "editor"; those are the
    parsed `authors` and `editors`. A month is stored as its full name from MONTHS.
    """

    key: str
    type: EntryType
    fields: dict[str, str] = field(default_factory=dict)
    authors: list[Name] = field(default_factory=list)
    editors: list[Name] = field(default_factory=list)


class ParseError(Exception):
    """A syntax error in an input file, with the 1-based line it was found on."""

    def __init__(self, message: str, line: int) -> None:
        super().__init__(f"line {line}: {message}")
        self.message = message
        self.line = line


@dataclass
class ParseResult:
    """What a reader returns: the entries in file order, any @preamble strings, and the errors."""

    entries: list[Entry] = field(default_factory=list)
    preamble: list[str] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)
