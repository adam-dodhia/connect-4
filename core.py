"""Core Connect 4 game logic, independent of any input/output method."""

from typing import List, Optional, Tuple

ROWS = 6
COLUMNS = 7
CONNECT_N = 4


class Connect4Game:
    def __init__(self) -> None:
        self.board: List[List[str]] = [["." for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.current_player: str = "X"
        self.move_history : List = []
        self.winner: Optional[str] = None
        self.game_over: bool = False
        self.winning_cells: Optional[List[Tuple[int, int]]] = None

    def is_valid_move(self, column: int) -> bool:
        """Return true if 1) input is in valid range of columns 2) this column isn't full"""
        return 0 <= column < COLUMNS and self.board[0][column] == "."

    def valid_moves(self) -> List[int]:
        """Return array of valid columns to drop a piece"""
        return [column for column in range(COLUMNS) if self.is_valid_move(column)]

    def make_move(self, column: int) -> int:
        """Drop the current player's piece into `column`. Returns the row it landed in."""
        if not self.is_valid_move(column):
            raise ValueError(f"Column {column} is not a valid move.")

        for row in range(ROWS - 1, -1, -1):
            if self.board[row][column] == ".":
                self.board[row][column] = self.current_player
                self.move_history.append(column)
                self._update_state_after_move(row, column)
                return row

        raise ValueError(f"Column {column} is full.")

    def undo_move(self) -> int:
        """Undoes the most recent move"""
        column = self.move_history.pop()

        for row in range(0, ROWS, 1):
            if self.board[row][column] == "X" or self.board[row][column] == "O":
                self.current_player = self.board[row][column]
                self.board[row][column] = "."
                self.winner = None
                self.winning_cells = None
                self.game_over = False
                return row

        raise ValueError(f"No move to undo found in {column}.")

    def is_draw(self) -> bool:
        return self.game_over and self.winner is None

    def clone(self) -> "Connect4Game":
        """Return an independent copy, for search algorithms to simulate moves on."""
        clone = Connect4Game()
        clone.board = [row.copy() for row in self.board]
        clone.current_player = self.current_player
        clone.move_history = self.move_history.copy()
        clone.winner = self.winner
        clone.game_over = self.game_over
        clone.winning_cells = list(self.winning_cells) if self.winning_cells is not None else None
        return clone

    def _update_state_after_move(self, row: int, column: int) -> None:
        winning_cells = self._find_winning_cells(row, column)
        if winning_cells is not None:
            self.winner = self.current_player
            self.winning_cells = winning_cells
            self.game_over = True
        elif not self.valid_moves():
            self.game_over = True
        else:
            self.winner = None
            self.winning_cells = None
            self.game_over = False
            self.current_player = "O" if self.current_player == "X" else "X"

    def _find_winning_cells(self, row: int, column: int) -> Optional[List[Tuple[int, int]]]:
        player = self.board[row][column]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for delta_row, delta_column in directions:
            line = [(row, column)]
            line = self._cells_in_direction(row, column, delta_row, delta_column, player) + line
            line = line + self._cells_in_direction(row, column, -delta_row, -delta_column, player)
            if len(line) >= CONNECT_N:
                return line
        return None

    def _cells_in_direction(
        self, row: int, column: int, delta_row: int, delta_column: int, player: str
    ) -> List[Tuple[int, int]]:
        cells = []
        r, c = row + delta_row, column + delta_column
        while 0 <= r < ROWS and 0 <= c < COLUMNS and self.board[r][c] == player:
            cells.append((r, c))
            r += delta_row
            c += delta_column
        return cells
