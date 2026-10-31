# listarc

Reads our mailing-list archives from mbox files: decodes headers and MIME bodies, threads the
conversations, searches them, and files messages into monthly archives, as a Perl library and a
command. Perl 5.36 or later with core modules only (`Encode`, `MIME::Base64`, `MIME::QuotedPrint`,
`Time::Local`, `Getopt::Long`, `File::Temp`); no CPAN dependencies. Run the tests with `prove -l t`.

## Model

`lib/Listarc/Model.pm` holds what the modules pass to one another: `parse_header_block`, the
classes `Listarc::Message` and `Listarc::Summary`, and the exception `Listarc::Error`. Each module
below uses only the model and nothing of its siblings; only the command uses them all. Every module
throws `Listarc::Error` for input it refuses, with the line of the input (or the column of a query)
where it found the problem.

A `Listarc::Message` holds bytes as they were in the archive; the modules that decode return Perl
character strings. Line endings are LF inside listarc: CRLF input is converted on reading.

## Mbox (`Listarc::Mbox`)

- `each_message($fh, $callback, %options)` reads an mbox from a filehandle one line at a time and
  calls `$callback->($message)` with each `Listarc::Message`, its `envelope` and `position` set. It
  never holds more than one message in memory: archives run to several gigabytes.
  `read_mbox($bytes, %options)` returns the list of messages in a string.
- A message starts at a separator line: `From` and a space, a sender with no spaces, and a date in
  the asctime form `Tue Oct 27 09:14:03 2026` (the day of the month may be padded with a space; a
  numeric zone such as `+0000` and a weekday that does not match are allowed). It counts only as the
  first line of the input or after an empty line; any other line that starts with `From` and a space
  is body text. The empty line before a separator belongs to the separator, not to the message
  before it, and so does an empty line at the end of the input.
- Input that does not start with a separator, after any empty lines, throws `not an mbox` with
  line 1. A message whose header block does not parse still becomes a message: its headers are
  whatever `parse_header_block` found.
- `variant` is `mboxrd` (the default), `mboxo` or `mboxcl2`. On reading, mboxrd removes one `>` from
  every body line matching `^>+From[ ]`, mboxo only from lines matching `^>From[ ]`, and mboxcl2
  removes none: it takes the body's length in bytes from `Content-Length`, and falls back to the
  separator rule when the header is missing or the bytes it names are not followed by an empty line
  and a separator, or by the end of the input.
- `write_mbox($fh, \@messages, %options)` writes `From`, a space and each message's envelope, or
  `MAILER-DAEMON Thu Jan  1 00:00:00 1970` when it has none, then its headers and body as `as_bytes`
  gives them, and an empty line. The body is quoted by the variant: mboxrd adds one `>` to every
  line matching `^>*From[ ]`, so `>From here` is written `>>From here`; mboxo adds one to lines
  matching `^From[ ]` only; mboxcl2 quotes nothing and writes `Content-Length` with the body's
  length, replacing any that was there. A message ends in exactly one LF before the empty line; one
  with none gets it.
- `envelope_date($envelope)` returns the separator's date as seconds since the epoch, read as UTC,
  or undef; `envelope_sender($envelope)` the sender.
- In mboxrd, messages whose bodies end in LF read back from what `write_mbox` wrote with the same
  headers and bodies; mboxo cannot promise that for a body line that starts `>From` and a space.

## MIME (`Listarc::MIME`)

- `parse_mime($message)` returns the message's part tree. A part is a hashref: `type`
  (`text/plain`, lower case), `params` (a hashref, names in lower case), `disposition` (`inline`,
  `attachment` or undef), `filename` (or undef), `headers` (pairs, as in a message), `body` (the
  decoded bytes) and, for a multipart, `parts`; a `message/rfc822` part has `message`, the part
  tree of the message it holds.
- `Content-Type` is `type/subtype` then `; name=value` parameters, values plain or in double quotes
  with backslash escapes; comments in parentheses are ignored. A missing or unreadable header means
  `text/plain; charset=us-ascii`, except inside a `multipart/digest`, where it means
  `message/rfc822`.
- RFC 2231 parameters: `name*=charset'language'percent-encoded` is decoded through the charset,
  and continuations `name*0`, `name*1`, ... are joined in numeric order, percent-decoding only the
  segments whose name ends in `*`. So `title*=us-ascii'en-us'This%20is%20%2A%2A%2Afun%2A%2A%2A` is
  `This is ***fun***`.
- A multipart's parts lie between lines `--BOUNDARY` and the closing `--BOUNDARY--`, either one
  allowed trailing whitespace. The line break before a boundary line belongs to the boundary. The
  preamble and epilogue are dropped. A closing line that never comes ends the last part at the end
  of the body; a multipart with no `boundary` parameter is read as `text/plain`. Parts nest to any
  depth.
- `Content-Transfer-Encoding`: `base64` ignores characters outside its alphabet and accepts missing
  padding; `quoted-printable` removes soft line breaks (`=` at the end of a line) and trailing
  whitespace on each line, decodes `=XX` in either case, and keeps any other `=` as written; `7bit`,
  `8bit`, `binary` and any unknown value leave the body as it is.
- `filename` is the `Content-Disposition` parameter `filename`, else the `Content-Type` parameter
  `name`, RFC 2231 decoded. One written in RFC 2047 form is left as it is for the caller.
- `text_of($part)` decodes a text part through its charset with `Encode`; a missing charset is
  `us-ascii`, an unknown one or bytes that are not valid in it are read as UTF-8, invalid bytes
  becoming U+FFFD.
- `main_text($tree)` is the text a reader sees: the first part in depth-first order that is
  `text/plain` and not an attachment, preferring, in a `multipart/alternative`, its `text/plain`
  part over the others; when there is none, the first `text/html` part as text. HTML becomes text by
  dropping `script` and `style` elements with their content, starting a new line at `br` and at the
  end of `p`, `div`, `li`, `tr` and `h1` to `h6`, writing a hyphen and a space before each `li`,
  removing every other tag, decoding named (`amp`, `lt`, `gt`, `quot`, `apos`, `nbsp`) and numeric
  entities, collapsing runs of spaces and of more than two line breaks, and trimming. No text part
  gives `''`.
- `attachments($tree)` lists every leaf part that has disposition `attachment`, a filename, or a
  type other than `text/*`, except the part `main_text` chose, as `{ filename, type, size }`, the
  size in decoded bytes, in depth-first order.

## Headers (`Listarc::Header`)

- `decode_words($value)` decodes RFC 2047 encoded words, `=?charset?B?...?=` and `=?charset?Q?...?=`
  (`_` is a space in Q; the charset may carry `*language`), and drops the whitespace between two
  adjacent encoded words: `=?UTF-8?Q?a?= =?UTF-8?Q?b?=` is `ab`. A word that does not decode stays
  as written. Bytes outside encoded words are read as UTF-8 when valid and as windows-1252
  otherwise. `=?ISO-8859-1?Q?Andr=E9?= Pirard` is `Andr`, U+00E9, a space and `Pirard`.
- `parse_addresses($value)` reads an RFC 5322 address list and returns `(\@addresses,
  \@problems)`. Addresses are `{ name, address }`: `Name <local@domain>`, a bare `local@domain`,
  `"Quoted, Name" <local@domain>`, `local@domain (Comment Name)`, the comment then serving as the
  name when there is no other, groups `Team: a@x.org, b@x.org;` (their members listed in place),
  and obsolete routes `<@relay.org:local@domain>`, the route dropped. Names go through
  `decode_words`; domains are lower-cased, local parts kept as written. Empty entries between
  commas are skipped; an entry with no `@` goes into `@problems`, as written, and is skipped.
- `parse_date($value)` reads an RFC 5322 date and returns `(epoch, offset_minutes)`, or an empty
  list for a date it cannot read. The weekday is optional and ignored when it does not match; the
  month is an English abbreviation in any case; a two-digit year is 2000 to 2049 for 00 to 49 and
  1950 to 1999 for 50 to 99; seconds are optional; the zone is `+hhmm` or `-hhmm`, or `UT`, `GMT`,
  `EST`, `EDT`, `CST`, `CDT`, `MST`, `MDT`, `PST` or `PDT`, and a single military letter or a
  missing zone is `-0000`, which counts as 0. Comments in parentheses are ignored.
  `Tue, 27 Oct 2026 09:14:03 -0700` is `(1793117643, -420)`.
- `format_date($epoch, $offset_minutes)` writes the RFC 5322 form back, as
  `Tue, 27 Oct 2026 09:14:03 -0700`.

## Threads (`Listarc::Thread`)

- `thread(\@messages)` builds conversations by the JWZ algorithm (jwz.org/doc/threading.html),
  steps 1 to 4, from `Message-ID`, `In-Reply-To` and `References` only: subjects play no part. It
  returns the root nodes; a node is `{ id, message, children }`, `message` undef for a message
  that is referred to but not in the archive.
- A message's id is the first `<...>` in its `Message-ID`, without the brackets. A message with
  none, or with an id an earlier message has, gets `listarc-N`, N its position, and stays a message
  of its own.
- Its references are every `<...>` in `References`, in order, then the first `<...>` in
  `In-Reply-To` when it is not already the last of them.
- Each pair of consecutive references is linked parent to child unless the child already has a
  parent or the link would make a loop; then the message's parent becomes its last reference,
  replacing any parent it had, unless that would make a loop.
- An empty node (no message) with no children is dropped. An empty node with children is replaced
  by its children, except among the roots, where it stays when it has two or more children.
- Roots and the children of every node are ordered by the smallest position of any message below
  them, themselves included.
- `flatten(\@roots)` returns `[depth, node]` pairs in reading order, roots at depth 0.
- It must handle 100000 messages and reply chains 10000 deep, so no recursion.

## Search (`Listarc::Search`)

- `compile($query)` returns an object whose `matches($summary)` says whether a `Listarc::Summary`
  matches. A query is terms separated by whitespace, all of which must match; `OR` (upper case)
  between two terms needs either; `-` before a term negates it; parentheses group. Negation binds
  tightest, then the implied AND, then OR.
- Terms: `from:TEXT` (in any From name or address), `to:TEXT` (To or Cc), `subject:TEXT`,
  `body:TEXT`, `id:ID` (the whole message id), `has:attachment`, `filename:GLOB` (`*` and `?`, on
  any attachment), and `before:DATE`, `after:DATE` and `on:DATE`, DATE being `YYYY-MM-DD` or
  `YYYY-MM` (the whole month) in UTC. `after:D` is from D's first second on, `before:D` up to D's
  first second, `on:D` within D. A message with no date matches no date term. A bare word matches
  the subject, the body, or any name or address.
- TEXT is a word or a double-quoted phrase, matched as a substring with Unicode case folding.
- Errors, thrown with the column (from 1) where they start: an empty query, unbalanced
  parentheses, an `OR` with nothing on one side, a bad date, an unknown field (`foo:bar`, where
  `foo` is letters and not a field name; a word such as `10:30` is a bare word), an unclosed quote.

## Command (`bin/listarc`)

- `listarc index [--query Q] MBOX` prints one line per message, tab-separated: the position, the
  date as `YYYY-MM-DD HH:MM` in UTC (or `-` when it has none), the first sender's name or else
  address, and the subject.
- `listarc threads [--query Q] MBOX` prints each thread from `flatten`, two spaces of indent per
  level, a message as its position, sender and subject, and a missing one as `[missing <id>]`. With
  `--query`, a thread holding a match is printed whole.
- `listarc show MBOX N` prints the decoded From, To, Cc, Date and Subject, an empty line, the main
  text, then one `[attachment: NAME (TYPE, N bytes)]` line per attachment.
- `listarc extract MBOX N DIR` writes message N's attachments into DIR. Names have RFC 2047 words
  decoded, path separators and control characters replaced with `_` and leading dots removed; an
  empty name becomes `attachment-K`, K counting from 1; a taken name gets a space and `(2)`, `(3)`
  and so on before its extension. No existing file is overwritten.
- `listarc archive [--variant V] MBOX DIR` appends each message to `DIR/YYYY-MM.mbox` by its Date
  header in UTC, else its envelope date, else to `DIR/undated.mbox`, in input order, written in
  the variant given (mboxrd by default).
- `index` and `archive` read the mbox with `each_message`, so neither holds the whole archive in
  memory. A summary is built from the
  `Listarc::Header` and `Listarc::MIME` results: addresses from From, To and Cc, the decoded
  Subject, the Date (else the envelope date), the main text and the attachments.

A message number out of range, or an mbox that cannot be read, prints `listarc: FILE: line N:
message` (or `listarc: message`) to stderr and exits 1. A usage error exits 2, and so does a bad
query, printed as `listarc: query: column N: message`.

## Status

Only the model exists. Each module gets its own test file in `t/`.
