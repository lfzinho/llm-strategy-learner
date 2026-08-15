from constants import Move
from abc import ABC, abstractmethod


class Player(ABC):
    def __init__(self, name=None):
        self.name = name
        self.run_score = 0
        self.score = 0
        self.strategy_name = "None"
        self.game_history = []
        self.survivability = 0.0

    @abstractmethod
    def play(self) -> Move:
        """Returns either Move.COOPERATE or Move.DEFECT"""
        pass

    def update_score(self, score):
        self.score += score

    def update_history(self, moves):
        self.game_history.append(moves)

    def finish_game(self):
        self.run_score += self.score
        self.score = 0
        self.game_history = []

    def copy(self):
        return self.__class__()
