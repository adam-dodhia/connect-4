"""Player input handling, kept separate from core game logic.

`Player` is the interface future AI implementations should subclass -
only `get_move` needs to be implemented.
"""

from abc import ABC, abstractmethod

from connect4.core import COLUMNS, Connect4Game


class Player(ABC):
    def __init__(self, name: str, symbol: str) -> None:
        self.name = name
        self.symbol = symbol

    @abstractmethod
    def get_move(self, game: Connect4Game) -> int:
        """Return a valid, zero-indexed column for this player to play."""


class HumanPlayer(Player):
    def get_move(self, game: Connect4Game) -> int:
        while True:
            raw_input_value = input(f"{self.name} ({self.symbol}), choose a column (1-{COLUMNS}): ")
            try:
                column = int(raw_input_value) - 1
            except ValueError:
                print("Please enter a number.")
                continue

            if not game.is_valid_move(column):
                print("That column is full or out of range. Try again.")
                continue

            return column
