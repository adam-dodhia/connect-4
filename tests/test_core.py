"""Tests for connect4_game.py.

Run from the folder containing both files:
    pytest                 # run everything
    pytest -v              # list every test by name
    pytest -k undo         # only tests whose name contains "undo"
    pytest -x              # stop at the first failure
"""

import random

import pytest

from connect4.core import COLUMNS, ROWS, Connect4Game, _alignment

# --------------------------------------------------------------------------
# Fixtures and helpers
# --------------------------------------------------------------------------


@pytest.fixture
def game():
    """A fresh game. Any test that takes a `game` parameter receives a new one,
    so tests can never leak state into each other."""
    return Connect4Game()


def play(game: Connect4Game, moves: str) -> Connect4Game:
    """Play a string of 0-indexed columns, e.g. "0101010". Returns the game."""
    for ch in moves:
        game.make_move(int(ch))
    return game


def has_four(board, symbol) -> bool:
    """Slow but obviously-correct win check on the grid, used as a reference
    ("oracle") to cross-check the bitboard logic."""
    for r in range(ROWS):
        for c in range(COLUMNS):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                cells = [(r + k * dr, c + k * dc) for k in range(4)]
                if all(0 <= rr < ROWS and 0 <= cc < COLUMNS and board[rr][cc] == symbol
                       for rr, cc in cells):
                    return True
    return False


# Shared test data: (moves, expected winning cells). Used by several tests.
WINS = {
    "horizontal": ("0011223", [(5, 0), (5, 1), (5, 2), (5, 3)]),
    "vertical": ("0101010", [(5, 0), (4, 0), (3, 0), (2, 0)]),
    "diagonal /": ("01122323353", [(5, 0), (4, 1), (3, 2), (2, 3)]),
    "diagonal \\": ("65544343313", [(5, 6), (4, 5), (3, 4), (2, 3)]),
}
DRAW = "361313645534311043046626105524515600224220"  # a full board, no winner


# --------------------------------------------------------------------------
# A new game
# --------------------------------------------------------------------------


def test_new_game_is_empty(game):
    assert game.board == [["."] * COLUMNS for _ in range(ROWS)]
    assert game.move_history == []
    assert game.valid_moves() == list(range(COLUMNS))


def test_new_game_state(game):
    assert game.current_player == "X"
    assert game.winner is None
    assert not game.game_over
    assert not game.is_draw()
    assert game.winning_cells is None


# --------------------------------------------------------------------------
# Making moves
# --------------------------------------------------------------------------


def test_pieces_stack_from_the_bottom(game):
    # make_move returns the row the piece landed in (row 0 is the top).
    assert [game.make_move(3) for _ in range(ROWS)] == [5, 4, 3, 2, 1, 0]


def test_players_alternate(game):
    assert game.current_player == "X"
    game.make_move(0)
    assert game.current_player == "O"
    game.make_move(0)
    assert game.current_player == "X"
    assert game.board[5][0] == "X" and game.board[4][0] == "O"


@pytest.mark.parametrize("column", [-1, COLUMNS, 100])
def test_out_of_range_column_is_rejected(game, column):
    assert not game.is_valid_move(column)
    with pytest.raises(ValueError):
        game.make_move(column)


def test_full_column_is_rejected(game):
    play(game, "222222")
    assert not game.is_valid_move(2)
    assert 2 not in game.valid_moves()
    with pytest.raises(ValueError):
        game.make_move(2)


def test_failed_move_changes_nothing(game):
    play(game, "222222")
    before = (game.current, game.mask, list(game.move_history))
    with pytest.raises(ValueError):
        game.make_move(2)
    assert (game.current, game.mask, game.move_history) == before


# --------------------------------------------------------------------------
# Winning
# --------------------------------------------------------------------------


@pytest.mark.parametrize("moves, cells", WINS.values(), ids=WINS.keys())
def test_each_direction_wins(game, moves, cells):
    play(game, moves)
    assert game.winner == "X"
    assert game.game_over
    assert not game.is_draw()
    assert sorted(game.winning_cells) == sorted(cells)


@pytest.mark.parametrize("moves, cells", WINS.values(), ids=WINS.keys())
def test_no_win_one_move_earlier(game, moves, cells):
    play(game, moves[:-1])
    assert game.winner is None
    assert not game.game_over


@pytest.mark.parametrize("moves, cells", WINS.values(), ids=WINS.keys())
def test_is_winning_move_predicts_without_mutating(game, moves, cells):
    play(game, moves[:-1])
    before = (game.current, game.mask, list(game.move_history))
    assert game.is_winning_move(int(moves[-1]))
    assert (game.current, game.mask, game.move_history) == before


def test_o_can_win(game):
    play(game, "60101010")  # X wastes a move in column 6, then O stacks column 0 first
    assert game.winner == "O"
    assert game.current_player == "O"


def test_five_in_a_row_reports_all_five_cells(game):
    play(game, "001122443")  # X fills 0,1,2,4 then 3 joins them
    assert game.winner == "X"
    assert sorted(game.winning_cells) == [(5, c) for c in range(5)]


def test_line_does_not_wrap_between_columns():
    # X on the top two cells of column 0 and the bottom two of column 1.
    # In bit order these are 4, 5, 7, 8: only the sentinel bit 6 separates them.
    pos = (1 << 4) | (1 << 5) | (1 << 7) | (1 << 8)
    assert not _alignment(pos)


def test_no_moves_after_game_over(game):
    play(game, WINS["vertical"][0])
    with pytest.raises(ValueError):
        game.make_move(3)


# --------------------------------------------------------------------------
# Draws
# --------------------------------------------------------------------------


def test_full_board_is_a_draw(game):
    play(game, DRAW)
    assert game.is_draw()
    assert game.game_over
    assert game.winner is None
    assert game.valid_moves() == []
    assert all(cell != "." for row in game.board for cell in row)


# --------------------------------------------------------------------------
# Undo
# --------------------------------------------------------------------------


def test_undo_on_empty_game_raises(game):
    with pytest.raises(ValueError):
        game.undo_move()


def test_undo_returns_same_row_as_move(game):
    row = game.make_move(4)
    assert game.undo_move() == row


@pytest.mark.parametrize("moves", [w[0] for w in WINS.values()] + [DRAW])
def test_undo_everything_restores_empty_game(game, moves):
    play(game, moves)
    while game.move_history:
        game.undo_move()
    fresh = Connect4Game()
    assert (game.current, game.mask) == (fresh.current, fresh.mask)
    assert game.board == fresh.board


def test_undo_after_win_reopens_game(game):
    play(game, WINS["horizontal"][0])
    game.undo_move()
    assert game.winner is None
    assert not game.game_over
    assert game.current_player == "X"  # X gets the winning move back


# --------------------------------------------------------------------------
# Clone and key
# --------------------------------------------------------------------------


def test_clone_is_independent(game):
    play(game, "3344")
    copy = game.clone()
    copy.make_move(5)
    assert len(game.move_history) == 4
    assert game.board != copy.board


def test_key_same_position_by_different_move_orders():
    # X at 0 and 2, O at 1 and 3, reached in two different orders.
    a = play(Connect4Game(), "0123")
    b = play(Connect4Game(), "2301")
    assert a.board == b.board
    assert a.key() == b.key()


def test_key_differs_when_pieces_differ():
    a = play(Connect4Game(), "01")
    b = play(Connect4Game(), "10")  # same cells filled, colours swapped
    assert a.key() != b.key()


# --------------------------------------------------------------------------
# Randomised cross-check against the slow grid oracle
# --------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(50))
def test_random_game_matches_grid_oracle(seed):
    rng = random.Random(seed)  # seeded: a failure is reproducible
    game = Connect4Game()
    while not game.game_over:
        mover = game.current_player
        predicted = game.is_winning_move(column := rng.choice(game.valid_moves()))
        game.make_move(column)
        board = game.board
        assert has_four(board, mover) == predicted == (game.winner == mover)
        assert sum(cell != "." for row in board for cell in row) == len(game.move_history)