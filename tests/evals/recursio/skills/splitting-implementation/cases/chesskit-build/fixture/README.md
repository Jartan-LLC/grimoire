# chesskit

Chess tooling for our club's game archive: reads and writes FEN, generates legal moves and counts
them with perft, reads PGN files, and runs game clocks, as a library and a command.

## Types

`src/chesskit/model.py` holds the types the modules pass to one another: `Color`, `PieceType`,
`Piece`, `Square` (0 to 63, a1 = 0, h8 = 63) with the `FILES`, `RANKS` and `SQUARE_NAMES`
constants, `Move`, `Position`, `STARTING_FEN` and `ChessError`. Its docstrings settle the
conventions, such as how castling is written as a move and when the en passant square is set.
Every module below works on these and nothing else of its siblings, except the command, which uses
them all.

## FEN (`chesskit.fen`)

- `parse_fen(text)` returns a `Position`. Leading and trailing spaces are dropped and the fields
  are separated by single spaces. Six fields, or four, in which case the clocks are 0 and 1.
  Every error raises `ChessError` with a message that starts with the field at fault:
  `placement:`, `side:`, `castling:`, `en passant:`, `halfmove:`, `fullmove:`, or `position:` for
  a rule across fields.
  - **Placement**: eight ranks separated by `/`, rank 8 first. Each rank is piece letters
    (`pnbrqk`, uppercase for White) and digits 1 to 8 for runs of empty squares, adding up to 8
    squares, with no two digits in a row: `placement: rank 3 has 9 squares`.
  - **Side**: `w` or `b`.
  - **Castling**: `-`, or a non-empty subset of `KQkq` in that order without repeats.
  - **En passant**: `-`, or a square on rank 6 with White to move or rank 3 with Black to move.
    The pawn that just advanced must stand on the square in front of it, seen from the side to
    move (e5 for e6), and the square itself and the one behind it (e7 for e6) must be empty.
  - **Clocks**: the halfmove clock is a whole number from 0, the fullmove number from 1, both
    plain digits without a sign. The halfmove clock must be 0 when an en passant square is set.
  - **Position**: exactly one king of each color; no pawn on rank 1 or 8; at most 8 pawns and 16
    pieces a side; each castling right needs the king on its home square (e1 or e8) and the rook
    in its corner (h1 for `K`, a1 for `Q`, h8 for `k`, a8 for `q`).
- `write_fen(position)` always writes six fields, castling letters in `KQkq` order, `-` for no
  rights or no en passant square. `write_fen(parse_fen(text)) == text` for every valid six-field
  FEN.
- `render_board(position, flipped=False)` returns nine lines: the ranks from 8 down, each the rank
  digit, a space and the eight squares as FEN letters (`.` for empty) separated by spaces, then
  two spaces and `a b c d e f g h`. With `flipped` the board is seen from Black's side: rank 1 first and the
  files from h to a.

## Move generation (`chesskit.movegen`)

- `legal_moves(position)` returns every legal move for the side to move, sorted by their UCI
  strings. A move is legal when it does not leave the mover's own king attacked.
  - **Pawns**: one square forward onto an empty square, two from the starting rank when both
    squares are empty, diagonal captures, and a move to the last rank as four moves, one per
    promotion piece (queen, rook, bishop, knight).
  - **En passant**: a pawn on the fifth rank (fourth for Black) beside the en passant square's
    file captures onto that square and removes the advanced pawn. It is illegal when removing
    both pawns from the rank opens a line from a rook or queen to the capturer's king: in
    `8/8/8/KPp4r/8/8/8/7k w - c6 0 2`, b5 takes c6 is not a legal move.
  - **Castling**: with the right kept, king and rook on their home squares and every square
    between them empty, and the king not in check, not passing through an attacked square and not
    landing on one: f1 and g1 for White king-side, d1 and c1 for queen-side (b1 need only be
    empty), and the same on rank 8 for Black.
- `make_move(position, move)` returns the position after a legal move, or raises `ChessError` for
  an illegal one. It moves the rook when castling, removes the pawn taken en passant, and promotes.
  Castling rights go when the king moves, when a rook moves from its corner, and when anything is
  captured on a corner. The en passant square is set as the model's docstring says. The halfmove
  clock resets on a pawn move or capture and otherwise goes up by one; the fullmove number goes up
  after Black moves.
- `is_check(position)`, `is_checkmate(position)` (in check, no legal move) and
  `is_stalemate(position)` (not in check, no legal move).
- `uci(move)` writes a move as from-square, to-square and a lowercase promotion letter: `e2e4`,
  `e1g1`, `a7a8q`. `parse_uci(text)` reads one back; a malformed string raises `ChessError`.
- `perft(position, depth)` counts the leaf positions of the legal move tree to `depth` (depth 0 is
  1). `divide(position, depth)` returns the count under each legal first move, keyed by its UCI
  string. The tests check these published counts:

  | Position (FEN) | Depth 1 | Depth 2 | Depth 3 |
  |----------------|---------|---------|---------|
  | the starting position | 20 | 400 | 8902 |
  | `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1` | 48 | 2039 | 97862 |
  | `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1` | 14 | 191 | 2812 |
  | `r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1` | 6 | 264 | 9467 |
  | `rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8` | 44 | 1486 | 62379 |

  The third position also gives 43238 at depth 4.

## PGN (`chesskit.pgn`)

Reads the PGN export format's syntax only: moves are not played or checked for legality.

- `tokenize(text)` returns `Token(kind, text, line, column)`s, numbered from 1, of the kinds
  `TAG_OPEN`, `TAG_CLOSE`, `SYMBOL`, `STRING`, `MOVE_NUMBER`, `SAN`, `NAG`, `COMMENT`,
  `VARIATION_OPEN`, `VARIATION_CLOSE` and `RESULT`.
  - A string is in double quotes, with `\"` and `\\` as its only escapes, on one line.
  - A brace comment `{...}` may span lines and does not nest; its text is kept with the
    surrounding whitespace stripped. A `;` starts a comment that runs to the end of the line. A
    line whose first character is `%` is skipped entirely.
  - A move number is digits followed by one dot (`12.`) or three (`12...`).
  - A NAG is `$` and 0 to 255. The suffixes `!`, `?`, `!!`, `??`, `!?` and `?!` straight after a
    move become the NAGs 1, 2, 3, 4, 5 and 6.
  - A SAN token matches `[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](=[QRBN])?[+#]?`, or `O-O` and `O-O-O`
    with an optional `+` or `#`. `0-0` and `0-0-0` are read as castling and written with letters;
    `e8Q` is read as `e8=Q`. A promotion onto a rank other than 1 or 8 is an error.
  - The results are `1-0`, `0-1`, `1/2-1/2` and `*`.
  - Anything else raises `PgnError` (a `ChessError` subclass defined in this module) carrying
    the line and column, its message as `line 12, column 5: unexpected ")"`.
- `parse_games(text)` returns a list of `Game`s (defined in this module), several per file:
  - `tags`: a dict of the tag pairs `[Name "value"]` in file order. A name starts with a letter and
    holds letters, digits and underscores; a repeated name in one game is an error.
  - `moves`: the main line as a list of
    `MoveNode(san, number, color, nags, comment_before, comment_after, variations)`. `variations` holds the alternatives to that move, each a list of
    `MoveNode`s that may hold variations of its own, to any depth. A `(` before any move of its
    line is an error.
  - A comment before the first move of a game or variation is that move's `comment_before`; any
    other comment goes to the preceding move's `comment_after`, several joined by one space.
  - Move numbers are optional, but one that is present must match its move: `n.` before White's
    n-th move, `n...` before Black's. Numbering starts at White's first move unless the game has a
    `FEN` tag, in which case the first move number in the game sets it.
  - `result`: the game ends at its result token. When a `Result` tag is present the two must be
    the same; a game with no result before the end of the text is an error.
- `mainline(game)` returns the main line's SAN strings.

## Clocks (`chesskit.clock`)

- `parse_time_control(text)` reads a PGN `TimeControl` tag, extended with delays, and returns a
  `TimeControl` (defined in this module): a list of periods, each a move count (None for the rest
  of the game), its seconds, and an optional increment, simple delay or Bronstein delay. Periods are
  separated by `:`; a period is `[MOVES/]SECONDS` followed by at most one of `+N` (Fischer
  increment), `dN` (simple delay) or `bN` (Bronstein delay). Examples: `300+2`,
  `40/7200:3600+30`, `5400d10`, `180b2`. Only the last period may leave out the move count; a last
  period with a move count repeats (`40/7200` gives another 7200 seconds every 40 moves). `-` (no
  control) and `?` (unknown) return None. A sandclock (`*180`), zero seconds or zero moves raises
  `ChessError`.
- `describe(control)` writes each period as `40 moves in 2:00:00` or `rest of game in 1:00:00`,
  followed by a space and `+30s increment`, `10s delay` or `2s Bronstein delay` when it has one,
  and joins the periods with a comma and `then`. `40/7200:3600+30` gives
  `40 moves in 2:00:00, then rest of game in 1:00:00 +30s increment`.
- `format_seconds(seconds)` writes `H:MM:SS`, with a tenth after a dot when the time is not whole
  (`1:59:58.5`); `parse_clock(text)` reads that form back, as found in `[%clk 1:59:58.5]`
  comments.
- `Clock(control)` runs a game's clock. Both sides start with the first period's seconds.
  `move(color, used)` charges a move that took `used` seconds and returns a `MoveRecord(color, number, used,
  charged, remaining)`, `number` being that side's move count from 1. White moves first and the
  sides alternate, or `ChessError` is raised.
  - Simple delay `d`: the clock does not run for the first `d` seconds, so `charged` is
    `max(0, used - d)`.
  - Bronstein delay `d`: `charged` is `used`, then `min(used, d)` is given back.
  - Fischer increment `i`: `i` is added after every move of its period, the first included.
  - A side whose charge reaches or passes its remaining time has flagged: its remaining time is
    0, `flagged` returns its color, and any later move raises `ChessError`.
  - When a side completes the last move of a period, the next period's seconds are added to its
    clock, after that move's own increment.

  With `300+2`, a 10.5-second move leaves 291.5 + 2 = 293.5. With `300d5`, a 3-second move leaves
  300 and an 8-second one 297. With `300b5`, a 3-second move leaves 300 and an 8-second one 297.
- `time_spent(readings, control)` takes one side's clock readings after each of its moves, in
  seconds, and returns the time each move cost: the reading before (the starting time for the
  first move), plus the increment and any period time that move earned, minus the reading after.

## Command (`chesskit.cli`)

- `chesskit perft [--divide] FEN DEPTH` prints `Nodes: N`. With `--divide`, one line per first
  move comes before it, `e2e4: 20`, in UCI order, then a blank line. The time taken and the nodes
  per second go to stderr.
- `chesskit fen-check FEN` prints the board as `render_board` draws it, then
  `Side to move: white`, `Status: ok` (or `check`, `checkmate`, `stalemate`), `Legal moves: N`
  and `FEN:` followed by a space and the FEN as `write_fen` writes it.
- `chesskit pgn-stats FILE...` reads every game of every file and prints:
  - `Games: N` and `Results: 1-0 A, 0-1 B, 1/2-1/2 C, * D`.
  - `Average length: X plies` over the main lines, one decimal place, and
    `Longest: N plies (White - Black, Event)` from the tags, `?` for a missing tag.
  - `Openings:` with the five most common `ECO` codes and their counts, ties by code; games
    without the tag are left out.
  - `Time controls:` with each distinct `TimeControl` tag, its `describe` text and its count;
    `none` for `-` and `unknown` for `?`.
  - When games carry `[%clk ...]` comments, `Average time per move: white X s, black Y s`, one
    decimal place, from `time_spent` over each game's clock readings.

A bad FEN prints `chesskit: message` on stderr and exits 2 for `perft`, 1 for `fen-check`. A PGN
error prints `FILE:LINE:COLUMN: message` on stderr, the file's other games are still counted up to
the error, and the exit status is 1; a file that cannot be read gives 2. Otherwise the exit status
is 0.

## Status

Only the types exist.
