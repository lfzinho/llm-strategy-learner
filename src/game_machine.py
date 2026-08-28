import random
from constants import Move


class GameMachine:
    def __init__(self, payoff_matrix=None, error_rate=0.05):
        self.payoff_matrix = payoff_matrix or {
            Move.COOPERATE: {Move.COOPERATE: (3, 3), Move.DEFECT: (0, 5)},
            Move.DEFECT: {Move.COOPERATE: (5, 0), Move.DEFECT: (1, 1)},
        }
        self.error_rate = error_rate

    def get_payoff(self, player1_action, player2_action):
        return self.payoff_matrix[player1_action][player2_action]

    def _apply_noise(self, action: Move) -> tuple[Move, bool]:
        """Returns (executed_action, was_error). If error occurs, action is flipped."""
        if self.error_rate > 0 and random.random() < self.error_rate:
            flipped = Move.DEFECT if action == Move.COOPERATE else Move.COOPERATE
            return flipped, True
        return action, False

    def play_game(self, player1, player2):
        player1_action = player1.play()
        player2_action = player2.play()

        # Apply noise / error rate
        p1_executed, p1_error = self._apply_noise(player1_action)
        p2_executed, p2_error = self._apply_noise(player2_action)

        # Update history with executed moves and whether player's own move had an error
        # Tuple format: (my_executed_move, opp_executed_move, my_error, opp_error, my_intended_move)
        p1_history_entry = (p1_executed, p2_executed, p1_error, p2_error, player1_action)
        p2_history_entry = (p2_executed, p1_executed, p2_error, p1_error, player2_action)

        player1.update_history(p1_history_entry)
        player2.update_history(p2_history_entry)

        player1.update_score(self.get_payoff(p1_executed, p2_executed)[0])
        player2.update_score(self.get_payoff(p1_executed, p2_executed)[1])
