# zonekit

Reads DNS zone master files, checks them for the mistakes that break resolution, encodes them in
wire format, and compares two versions of a zone, as a library and a command.

## Data model

`src/zonekit/model.py` holds the records the modules pass to one another: the `RType` enum (its
values are the type codes), one rdata dataclass per type (`A`, `AAAA`, `CNAME`, `NS`, `MX`, `TXT`,
`SOA`, `SRV`, `CAA`), `Record`, `Zone`, `Problem` with its `Severity`, and `ZoneError`. Names are
absolute, lowercase and end in a dot. Every module below works on these and nothing else of its
siblings, except the command, which uses them all.

## Parser (`zonekit.parse`)

`parse_zone(text, origin)` reads an RFC 1035 master file and returns a `ParseResult`: the `Zone`
(with `origin` as its origin and the good records in file order) and a list of
`LineError(line, message)`, numbered from 1. A bad record is reported and skipped; parsing goes on.
`origin` must be absolute, or `ZoneError` is raised.

- **Comments and tokens**: a `;` outside a quoted string starts a comment that runs to the end of
  the line. Tokens are separated by spaces and tabs. A quoted string is one token and may hold
  spaces, `;`, `(` and `)`. Inside and outside quotes, `\X` stands for the character X and `\DDD`
  for the byte with decimal value DDD (exactly three digits, at most 255).
- **Parentheses**: `(` and `)` outside quotes let a record run over several lines; the newlines
  inside them are spaces. The record's line number is the line it starts on. Nested parentheses, a
  `)` with no `(`, and a `(` still open at the end of the file are line errors.
- **Directives**: `$ORIGIN name` sets the origin for the lines after it (a relative name is taken
  against the current origin). `$TTL ttl` sets the default TTL. `$INCLUDE` is refused with the line
  error `$INCLUDE is not supported`; any other `$` word is `unknown directive`.
- **Owner**: a line that starts with a space or tab has the previous record's owner; with no
  previous record that is a line error. `@` is the current origin. A name with no final dot is
  relative and gets the current origin appended. Names are lowercased. A label longer than 63
  characters, an empty label, a name over 253 characters, or a backslash in a name is a line error.
- **TTL and class**: after the owner come an optional TTL and an optional class, in either order,
  then the type. A TTL is a number of seconds or a sum of units, case-insensitive: `3600`, `1h`,
  `1h30m`, `2w` (`s`, `m`, `h`, `d`, `w`). With no TTL the record takes the last `$TTL`, or the
  previous record's TTL when there has been no `$TTL`, and with neither it is a line error. With
  no class the record takes the previous record's class; a class other than `IN` is a line error.
- **Types and rdata**: the type is an `RType` name, case-insensitive; any other word is
  `unknown type X`. The rdata fields, with a line error for a missing, extra or malformed field:
  - `A`: four decimal parts 0 to 255 without leading zeros.
  - `AAAA`: any form `ipaddress.IPv6Address` accepts, stored compressed.
  - `CNAME`, `NS`: one name, made absolute as owners are.
  - `MX`: a preference 0 to 65535 and a name.
  - `TXT`: one or more strings, quoted or bare, each at most 255 bytes after escapes.
  - `SOA`: two names, then the serial (0 to 4294967295, a plain number) and the refresh, retry,
    expire and minimum times (units allowed). The SOA's parentheses usually span lines.
  - `SRV`: priority, weight and port, each 0 to 65535, and a target name.
  - `CAA`: flags 0 to 255, a tag of letters and digits, and a value, quoted or bare, kept as bytes.

## Checks (`zonekit.validate`)

`validate(zone)` returns a list of `Problem`s, sorted by owner, then errors before warnings, then
message. Each check reports on the owner named here.

- **SOA**: no SOA is an error at the origin (`no SOA record`); more than one, or one whose owner is
  not the origin, is an error. A serial not of the form `YYYYMMDDnn`, ten digits whose first eight
  are a real calendar date from 1990 on, is a warning. The timers warn when retry is not below
  refresh, when expire is not above refresh plus retry, and when minimum is over 86400.
- **Apex NS**: no NS record at the origin is an error.
- **CNAME**: a CNAME beside any other record at the same owner (`CNAME and other data`), two
  CNAMEs at one owner, and a CNAME at the origin (`CNAME at the zone apex`) are errors.
- **Targets**: an MX exchange or an NS target that is the owner of a CNAME in the zone is an error
  on the MX or NS owner, as `MX points at a CNAME (mail.example.com.)`.
- **Glue**: an NS target at or below the origin with no A or AAAA record in the zone is an error,
  `no address record for in-zone name server ns1.example.com.`.
- **TTLs**: a TTL over 2147483647 is an error (RFC 2181 section 8); one under 60 or over 604800 is
  a warning. An RRset (the records of one owner and type) whose records have different TTLs is a
  warning (RFC 2181 section 5.2).
- **Duplicates**: a record with the same owner, type and rdata as an earlier one is a warning,
  once per extra copy.
- **SRV**: the owner must start with `_service._proto`: a service label of `_` and 1 to 15
  letters, digits or hyphens, and a protocol label of `_tcp`, `_udp`, `_tls` or `_sctp`; anything
  else is an error. A target of `.` beside other SRV records at the same owner is a warning.
- **CAA**: tags are compared case-insensitively. `issue`, `issuewild` and `iodef` are known; an
  unknown tag is a warning, or an error when the critical flag (128) is set. Flags other than 0 and
  128 are a warning. An `iodef` value that does not start with `mailto:` or `https://` is an error.
- **Out of zone**: a record whose owner is not at or below the origin is an error.

## Wire format (`zonekit.wire`)

- `encode_message(records, message_id=0)` returns a DNS message (RFC 1035 section 4) holding the
  records as answers: a 12-byte header (the id, flags `0x8400` for an authoritative response,
  QDCOUNT 0, ANCOUNT the number of records, NSCOUNT 0, ARCOUNT 0), then each record as owner, type
  code, class 1, TTL as an unsigned 32-bit number, RDLENGTH and rdata, all big-endian.
- **Names and compression**: a name is its labels, each a length byte and its bytes, then a zero
  byte. Before writing a name, find the longest suffix of it, on a label boundary, already written
  somewhere in the message at an offset below `0x4000`; write the labels before that suffix and
  then the two-byte pointer `0xC000 | offset`. Owners and the names inside NS, CNAME, SOA (both)
  and MX rdata are compressed. An SRV target is never compressed (RFC 2782), though later names can
  point into it.
- **Rdata**: A is 4 bytes and AAAA 16. MX is a 16-bit preference and a name. TXT is each string as
  a length byte and its bytes. SOA is two names and five 32-bit numbers. SRV is three 16-bit
  numbers and a name. CAA is the flags byte, the tag's length byte, the tag, and the value as the
  rest of the rdata.
- A label of more than 63 bytes, a name of more than 255 bytes in wire form, or a number that does
  not fit its field raises `ZoneError`.
- `decode_message(data)` returns `(message_id, records)`: question entries (name, type, class) are
  read and dropped, then the answer, authority and additional records are returned in that order.
  Names come back lowercase with a final dot. A pointer must point to an offset before itself, so
  a loop cannot form. Truncated data, a forward pointer, a label type other than plain or pointer,
  an unknown type code, a class other than 1, or an RDLENGTH that does not match the rdata read
  raises `WireError` (a `ZoneError` subclass defined in this module) with the offset where it
  happened.

Example: `example.com. 300 IN A 192.0.2.1` followed by
`example.com. 300 IN MX 10 mail.example.com.` encodes to 60 bytes; the second owner and the end of the exchange are both the
pointer `c0 0c`:

```text
0000  00 00 84 00 00 00 00 02 00 00 00 00 07 65 78 61
0010  6d 70 6c 65 03 63 6f 6d 00 00 01 00 01 00 00 01
0020  2c 00 04 c0 00 02 01 c0 0c 00 0f 00 01 00 00 01
0030  2c 00 09 00 0a 04 6d 61 69 6c c0 0c
```

## Zone comparison (`zonekit.diff`)

- `diff_zones(old, new)` compares two zones RRset by RRset and returns a `ZoneDiff` (defined in
  this module) of four lists of `RRsetChange(owner, rtype, old, new)`, `old` and `new` being the
  RRset's records on each side, and a list of warnings:
  - `added`: RRsets only in `new`; `removed`: RRsets only in `old`.
  - `changed`: RRsets in both whose sets of rdata differ.
  - `ttl_changed`: RRsets in both with the same rdata but a different TTL, kept apart from
    `changed`.
  - Each list is ordered by owner in DNS canonical order (RFC 4034 section 6.1: labels compared
    from the right, as lowercase bytes, a missing label first), then by type code. So
    `example.com.`, `a.example.com.`, `b.a.example.com.`, `z.example.com.`, `*.z.example.com.`.
  - When any RRset other than the SOA was added, removed or changed, or changed its TTL, and the
    new SOA serial is not greater than the old one under RFC 1982 serial arithmetic (s1 is less
    than s2 when `0 < (s2 - s1) mod 2^32 < 2^31`), the warnings hold
    `records changed but the SOA serial did not increase (2026103001 -> 2026103001)`.
- `rdata_text(rdata)` writes rdata as a master file would: names absolute, numbers in decimal, TXT
  and CAA values in double quotes with `"` and `\` escaped by a backslash and any byte outside
  0x20 to 0x7E written as `\DDD`. Examples: `10 mail.example.com.`, `"v=spf1 -all"`,
  `0 issue "ca.example.net"`.
- `render_diff(diff)` returns one line per record, RRsets in the canonical order across all four
  lists, and each RRset's records ordered by their rdata text: `- owner ttl IN TYPE rdata` for a
  removed record, then `+ owner ttl IN TYPE rdata` for an added one (a changed RRset shows its old
  records then its new ones), and `~ owner TYPE ttl 3600 -> 300` for a TTL-only change. Warnings
  follow, each as `! message`. No differences gives an empty string.

## Command (`zonekit.cli`)

Each file's origin is `--origin` when given, otherwise the file name with a final `.zone` or `.db`
removed and a dot added: `example.com.zone` has the origin `example.com.`.

- `zonekit check [--origin NAME] [--strict] FILE...` parses and checks each file. It prints each
  line error as `FILE:LINE: message`, each problem as `FILE: severity: owner: message`, and
  `FILE: N records, E errors, W warnings` on stderr. The exit status is 0 when no file has a line
  error or an error problem, 1 when one does (with `--strict`, a warning counts too), and 2 when a
  file cannot be read; the other files are still checked.
- `zonekit diff [--origin NAME] OLD NEW` prints `render_diff` of the two zones. It exits 0 when
  they are the same, 1 when they differ, and 2 when a file cannot be read or has line errors, which
  it prints as `check` does.
- `zonekit encode [--origin NAME] [--id N] [--out PATH] FILE` encodes the zone's records, in file
  order, as one message. With `--out` it writes the bytes to PATH; otherwise it prints a hex dump
  as in the example above: 16 bytes a row, the offset as four lowercase hex digits, two spaces, and
  the bytes as lowercase hex pairs separated by one space. A file with line errors prints them and
  exits 1 without encoding; an unreadable file exits 2; a `ZoneError` prints `zonekit: message` and
  exits 2.

## Status

Only the data model exists.
