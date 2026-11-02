"""Command line interface for Connect 4."""

from core import COLUMNS, Connect4Game
from players import HumanPlayer, Player
from models.random_agent import RandomModel
from models.minimax_agent import MinimaxModel

RESET = "\033[0m"
PIECE_COLOURS = {"X": "\033[91m", "O": "\033[93m"}  # bright red, bright yellow
HIGHLIGHTS = {"X": "\033[41m\033[30m", "O": "\033[43m\033[30m"}  # coloured background, black text
BAR_WIDTH = 20


def print_board(game: Connect4Game) -> None:
    winning_cells = set(game.winning_cells or [])

    for row_index, row in enumerate(game.board):
        cells = []
        for column_index, cell in enumerate(row):
            if cell == ".":
                cells.append(cell)
            elif (row_index, column_index) in winning_cells:
                cells.append(f"{HIGHLIGHTS[cell]}{cell}{RESET}")
            else:
                cells.append(f"{PIECE_COLOURS[cell]}{cell}{RESET}")
        print(" ".join(cells))
    print(" ".join(str(column + 1) for column in range(COLUMNS)))
    print()


def print_scores(scores: dict[int, float], chosen: int) -> None:
    """Bar chart of the AI's score per column; negative bars extend left of the axis."""
    peak = max((abs(score) for score in scores.values()), default=0) or 1

    print("AI move scores:")
    for column in range(COLUMNS):
        if column not in scores:
            print(f"{column + 1} {' ' * BAR_WIDTH}| full")
            continue

        score = scores[column]
        bar = "█" * round(abs(score) / peak * BAR_WIDTH)
        left = bar.rjust(BAR_WIDTH) if score < 0 else " " * BAR_WIDTH
        right = bar if score > 0 else ""
        marker = " <- chosen" if column == chosen else ""
        print(f"{column + 1} {left}|{right} {score}{marker}")
    print()


def play(players: dict[str, Player]) -> None:
    game = Connect4Game()
    print_board(game)

    while not game.game_over:
        player = players[game.current_player]
        column = player.get_move(game)
        if isinstance(player, MinimaxModel):
            print_scores(player.last_scores, column)
        game.make_move(column)
        print_board(game)

    if game.winner:
        print(f"{players[game.winner].name} wins!")
    else:
        print("It's a draw!")


def main() -> None:
    players: dict[str, Player] = {
        "X": MinimaxModel("Player 1", "X"),
        "O": MinimaxModel("Player 2", "O"),
    }
    play(players)


if __name__ == "__main__":
    main()