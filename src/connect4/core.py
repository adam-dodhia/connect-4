"""Core Connect 4 game logic, independent of any input/output method.

The board is a bitboard (Pascal Pons, "Solving Connect 4", Part 6):
two ints, `current` (stones of the player to move) and `mask` (all occupied
cells). Each column uses ROWS + 1 bits; the extra always-empty "sentinel" bit on
top stops lines wrapping from one column into the next.

    .  .  .  .  .  .  .     <- sentinel row
    5 12 19 26 33 40 47
    4 11 18 25 32 39 46
    3 10 17 24 31 38 45
    2  9 16 23 30 37 44
    1  8 15 22 29 36 43
    0  7 14 21 28 35 42     bit index = column * (ROWS + 1) + bit_row

Public coordinates are (row, column) with row 0 at the TOP of the board.

The only stored state is `current`, `mask` and `move_history`. Everything else
(winner, game_over, current_player, winning_cells) is derived from them, so
make_move/undo_move never have to keep extra fields in sync.
"""

from typing import List, Optional, Tuple

ROWS = 6
COLUMNS = 7
CONNECT_N = 4  # fixed: _alignment() is hard-wired for 4 in a row
CELLS = ROWS * COLUMNS
H1 = ROWS + 1  # bits per column (cells + sentinel)

# --- Precomputed masks (module level: faster to index than self.attributes) --
BOTTOM_MASK = tuple(1 << (c * H1) for c in range(COLUMNS))                  # lowest cell of a column
TOP_MASK = tuple(1 << (ROWS - 1 + c * H1) for c in range(COLUMNS))          # highest cell of a column
COLUMN_MASK = tuple(((1 << ROWS) - 1) << (c * H1) for c in range(COLUMNS))  # all cells of a column
BOTTOM_ALL = sum(BOTTOM_MASK)                                               # lowest cell of every column

# Bit distance to the neighbouring cell along each line:
#   horizontal = H1, vertical = 1, "\" diagonal = H1 - 1, "/" diagonal = H1 + 1
DIRECTION_SHIFTS = (H1, 1, H1 - 1, H1 + 1)


def _alignment(pos: int) -> bool:
    """True if `pos` (one player's stones) has 4 in a row.
    m = pos & (pos >> s) marks stones with a neighbour s bits away;
    m & (m >> 2s) then finds two such pairs back to back: 4 in a row."""
    for s in DIRECTION_SHIFTS:
        m = pos & (pos >> s)
        if m & (m >> (2 * s)):
            return True
    return False


def _bit_to_cell(bit_index: int) -> Tuple[int, int]:
    """Bit index -> (row, column), row 0 at the top."""
    column, bit_row = divmod(bit_index, H1)
    return ROWS - 1 - bit_row, column


class Connect4Game:
    def __init__(self) -> None:
        self.current: int = 0  # stones of the player to move
        self.mask: int = 0     # every occupied cell
        self.move_history: List[int] = []

    # --- moves -------------------------------------------------------------
    def is_valid_move(self, column: int) -> bool:
        """Return true if 1) input is in valid range of columns 2) this column isn't full"""
        return 0 <= column < COLUMNS and not (self.mask & TOP_MASK[column])

    def valid_moves(self) -> List[int]:
        """Return array of valid columns to drop a piece"""
        return [column for column in range(COLUMNS) if not (self.mask & TOP_MASK[column])]

    def is_winning_move(self, column: int) -> bool:
        """Would dropping in `column` win for the player to move? (no mutation)"""
        if not self.is_valid_move(column):
            return False
        stone = (self.mask + BOTTOM_MASK[column]) & COLUMN_MASK[column]
        return _alignment(self.current | stone)

    def make_move(self, column: int) -> int:
        """Drop the current player's piece into `column`. Returns the row it landed in."""
        if self.game_over:
            raise ValueError("The game is over.")
        if not self.is_valid_move(column):
            raise ValueError(f"Column {column} is not a valid move.")
        # Flip perspective first, so the new stone belongs to the player who moved.
        self.current ^= self.mask
        # Carry trick: +1 at the column's bottom lands on its first empty cell.
        self.mask |= self.mask + BOTTOM_MASK[column]
        self.move_history.append(column)
        return ROWS - self._height(column)

    def undo_move(self) -> int:
        """Undoes the most recent move. Returns the row the removed piece was in."""
        if not self.move_history:
            raise ValueError("No move to undo.")
        column = self.move_history.pop()
        row = ROWS - self._height(column)
        self.mask ^= self._top_stone(column)  # reverse make_move in the opposite order
        self.current ^= self.mask
        return row

    # --- derived state -------------------------------------------------------
    @property
    def winner(self) -> Optional[str]:
        """The game stops at the first win, so only the last mover can have one."""
        if self.move_history and _alignment(self.current ^ self.mask):
            return "X" if len(self.move_history) % 2 == 1 else "O"
        return None

    @property
    def game_over(self) -> bool:
        return len(self.move_history) == CELLS or self.winner is not None

    def is_draw(self) -> bool:
        return len(self.move_history) == CELLS and self.winner is None

    @property
    def current_player(self) -> str:
        """Player to move; once the game is over, the player who made the last move."""
        n = len(self.move_history) - (1 if self.game_over else 0)
        return "X" if n % 2 == 0 else "O"

    @property
    def winning_cells(self) -> Optional[List[Tuple[int, int]]]:
        """Full winning line through the last stone played (can be 5+ long)."""
        if self.winner is None:
            return None
        pos = self.current ^ self.mask
        stone = self._top_stone(self.move_history[-1])
        for s in DIRECTION_SHIFTS:
            # Grow outwards from the last stone onto the winner's stones until
            # it stops changing. The empty sentinel row stops wrapping.
            line = stone
            while (grown := line | (((line << s) | (line >> s)) & pos)) != line:
                line = grown
            if line.bit_count() >= CONNECT_N:
                return [_bit_to_cell(i) for i in range(line.bit_length()) if line >> i & 1]
        return None  # unreachable: winner implies a line through the last stone

    @property
    def board(self) -> List[List[str]]:
        """Grid view for display code: board[row][column], row 0 at the top,
        cells "X", "O" or ".". Built on demand; don't use it in search loops."""
        x_stones = self.current if len(self.move_history) % 2 == 0 else self.current ^ self.mask
        return [
            ["." if not self.mask & bit else "X" if x_stones & bit else "O"
             for bit in (1 << (c * H1 + ROWS - 1 - row) for c in range(COLUMNS))]
            for row in range(ROWS)
        ]

    def key(self) -> int:
        """Unique integer for this position (e.g. for a transposition table)."""
        return self.current + self.mask + BOTTOM_ALL

    def clone(self) -> "Connect4Game":
        """Return an independent copy, for search algorithms to simulate moves on."""
        clone = Connect4Game()
        clone.current, clone.mask = self.current, self.mask
        clone.move_history = self.move_history.copy()
        return clone

    # --- helpers -------------------------------------------------------------
    def _height(self, column: int) -> int:
        """Number of stones in `column`."""
        return (self.mask & COLUMN_MASK[column]).bit_count()

    def _top_stone(self, column: int) -> int:
        """Bit of the highest stone in `column` (stones are a solid block from the bottom)."""
        return 1 << ((self.mask & COLUMN_MASK[column]).bit_length() - 1)