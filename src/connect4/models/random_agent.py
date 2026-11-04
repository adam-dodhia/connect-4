from connect4.players import Player
import random

class RandomModel(Player):
    def get_move(self, game):
        valid_moves = self.get_valid_moves(game)
        chosen_move = random.sample(valid_moves, 1)[0]
        return chosen_move