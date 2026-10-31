"""The types the chesskit modules pass to one another.

Squares are numbered 0 to 63 from White's side: a1 is 0, b1 is 1, h1 is 7, a2 is 8 and h8
is 63, so a square's file is `square % 8` and its rank `square // 8`, both counted from 0.
`SQUARE_NAMES[square]` is its algebraic name.
"""

import enum
from dataclasses import dataclass

Square = int

FILES = "abcdefgh"
RANKS = "12345678"
SQUARE_NAMES = tuple(file + rank for rank in RANKS for file in FILES)

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class ChessError(ValueError):
    """Input the chess tools cannot work with: a bad FEN, an illegal move, and so on."""


class Color(enum.Enum):
    """A side; the value is its FEN letter."""

    WHITE = "w"
    BLACK = "b"


class PieceType(enum.Enum):
    """A kind of piece; the value is its lowercase FEN letter."""

    PAWN = "p"
    KNIGHT = "n"
    BISHOP = "b"
    ROOK = "r"
    QUEEN = "q"
    KING = "k"


@dataclass(frozen=True)
class Piece:
    """A piece of one side. In FEN its letter is `kind.value`, uppercase for White."""

    color: Color
    kind: PieceType


@dataclass(frozen=True)
class Move:
    """A move from one square to another.

    Castling is written as the king's two-square move (e1 to g1 for White king-side); an en
    passant capture as the pawn's diagonal move to the en passant square. `promotion` is the
    piece a pawn becomes on the last rank, and None for every other move.
    """

    from_square: Square
    to_square: Square
    promotion: PieceType | None = None


@dataclass(frozen=True)
class Position:
    """Everything a FEN records about a position.

    `board` maps each occupied square to its piece; empty squares are absent.

    `castling` holds the rights still kept, as FEN letters: `K` and `Q` for White king-side
    and queen-side, `k` and `q` for Black. A right says the king and that rook have not
    moved; it does not say castling is legal now.

    `en_passant` is the square a pawn passed over on a two-square advance made on the
    previous move. It is set after every such advance, whether or not the other side has a
    pawn that could capture there, as FEN records it, and is None after any other move.

    `halfmove_clock` counts half-moves since the last capture or pawn move.
    `fullmove_number` starts at 1 and goes up after each of Black's moves.
    """

    board: dict[Square, Piece]
    side_to_move: Color
    castling: frozenset[str]
    en_passant: Square | None
    halfmove_clock: int
    fullmove_number: int
