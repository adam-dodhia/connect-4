from players import Player
import math

class MinimaxModel(Player):
    DEPTH = 8
    WIN_SCORE = 999
    CENTRE_OUT_MOVES = [3, 2, 4, 1, 5, 0, 6]

    def get_move(self, game):
        best_score, best_move = -math.inf, None
        self.last_scores = {}

        # Full window per root move so every column gets an exact score, not a pruned bound.
        for move in self.sort_moves(game.valid_moves()):
            game.make_move(move)
            score = -self.negamax(game, self.DEPTH - 1, -math.inf, math.inf)
            game.undo_move()

            self.last_scores[move] = score
            if score > best_score:
                best_score, best_move = score, move

        return best_move

    def negamax(self, game, depth, alpha, beta) -> float:
        if depth == 0 or game.game_over:
            return self.evaluate_board(game, depth)

        best_score = -math.inf
        for move in self.sort_moves(game.valid_moves()):
            game.make_move(move)
            score = -self.negamax(game, depth - 1, -beta, -alpha)
            game.undo_move()

            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_score

    def sort_moves(self, valid_moves):
        return [move for move in self.CENTRE_OUT_MOVES if move in valid_moves]

    def evaluate_board(self, game, depth) -> float:
        """Score from the point of view of the player to move.

        A terminal winner is the player who just moved, so the side to move
        has lost. `depth` favours faster wins and slower losses.
        """
        if game.game_over:
            if game.winner is None:
                return 0
            return -(self.WIN_SCORE + depth)

        me = game.current_player
        opp = "O" if me == "X" else "X"
        centre = [row[3] for row in game.board]
        return 3 * (centre.count(me) - centre.count(opp))
