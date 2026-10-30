import dataclasses

import pytest

from chesskit import SQUARE_NAMES, Color, Move, Piece, PieceType, Position


def test_squares_count_from_a1_along_the_ranks():
    assert SQUARE_NAMES[0] == "a1"
    assert SQUARE_NAMES[28] == "e4"
    assert SQUARE_NAMES[63] == "h8"


def test_a_move_is_no_promotion_by_default():
    assert Move(12, 28).promotion is None


def test_a_position_cannot_be_changed():
    kings = {4: Piece(Color.WHITE, PieceType.KING), 60: Piece(Color.BLACK, PieceType.KING)}
    p = Position(kings, Color.WHITE, frozenset(), None, 0, 1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.side_to_move = Color.BLACK  # type: ignore[misc]
