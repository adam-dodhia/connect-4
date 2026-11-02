"""Monte Carlo Tree Search agent with random rollouts.

Stands in for a full minimax solver (as in https://blog.gamesolver.org/) while
that's being built out: unlike depth-limited minimax, MCTS gives a playable,
benchmarkable agent at any iteration count, so later optimisations (better
rollout policy, UCT tuning, eventually grafting in exact end-game solving)
can be measured incrementally instead of landing all at once.
"""

import math
import random

from players import Player


def _other(symbol: str) -> str:
    return "O" if symbol == "X" else "X"


class MCTSNode:
    __slots__ = ("game", "parent", "move", "children", "untried_moves", "visits", "wins", "player_who_moved")

    def __init__(self, game, parent=None, move=None):
        self.game = game
        self.parent = parent
        self.move = move
        self.children: dict[int, "MCTSNode"] = {}
        self.untried_moves = game.valid_moves()
        self.visits = 0
        self.wins = 0.0
        # the player whose move produced this node's position (None for the root)
        self.player_who_moved = None if parent is None else _other(game.current_player)


class MCTSModel(Player):
    def __init__(self, name: str, symbol: str, iterations: int = 1000, exploration: float = math.sqrt(2)) -> None:
        super().__init__(name, symbol)
        self.iterations = iterations
        self.exploration = exploration

    def get_move(self, game) -> int:
        root = MCTSNode(game.clone())

        for _ in range(self.iterations):
            node = self._select(root)
            node = self._expand(node)
            winner = self._rollout(node.game.clone())
            self._backpropagate(node, winner)

        best_move, _ = max(root.children.items(), key=lambda item: item[1].visits)
        return best_move

    def _select(self, node: MCTSNode) -> MCTSNode:
        while not node.untried_moves and node.children:
            node = self._select_child(node)
        return node

    def _select_child(self, node: MCTSNode) -> MCTSNode:
        log_parent_visits = math.log(node.visits)

        def ucb1(child: MCTSNode) -> float:
            exploitation = child.wins / child.visits
            exploration = self.exploration * math.sqrt(log_parent_visits / child.visits)
            return exploitation + exploration

        return max(node.children.values(), key=ucb1)

    def _expand(self, node: MCTSNode) -> MCTSNode:
        if not node.untried_moves or node.game.game_over:
            return node

        move = random.choice(node.untried_moves)
        node.untried_moves.remove(move)

        child_game = node.game.clone()
        child_game.drop_piece(move)
        child = MCTSNode(child_game, parent=node, move=move)
        node.children[move] = child
        return child

    def _rollout(self, game) -> str | None:
        while not game.game_over:
            move = random.choice(game.valid_moves())
            game.drop_piece(move)
        return game.winner

    def _backpropagate(self, node: MCTSNode | None, winner: str | None) -> None:
        while node is not None:
            node.visits += 1
            if node.player_who_moved is not None:
                node.wins += self._score(winner, node.player_who_moved)
            node = node.parent

    @staticmethod
    def _score(winner: str | None, player: str) -> float:
        if winner is None:
            return 0.5
        return 1.0 if winner == player else 0.0
