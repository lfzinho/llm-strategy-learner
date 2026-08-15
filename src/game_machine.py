from constants import Move


class GameMachine:
    def __init__(self, payoff_matrix=None):
        self.payoff_matrix = payoff_matrix or {
            Move.COOPERATE: {Move.COOPERATE: (3, 3), Move.DEFECT: (0, 5)},
            Move.DEFECT: {Move.COOPERATE: (5, 0), Move.DEFECT: (1, 1)},
        }

    def get_payoff(self, player1_action, player2_action):
        return self.payoff_matrix[player1_action][player2_action]

    def play_game(self, player1, player2):
        player1_action = player1.play()
        player2_action = player2.play()
        player1.update_history((player1_action, player2_action))
        player2.update_history((player2_action, player1_action))
        player1.update_score(self.get_payoff(player1_action, player2_action)[0])
        player2.update_score(self.get_payoff(player1_action, player2_action)[1])
