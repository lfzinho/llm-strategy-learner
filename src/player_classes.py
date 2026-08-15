from player import Player
from constants import Move
import random


class AlwaysCooperatePlayer(Player):
    """Always cooperates"""

    def __init__(self, name=None):
        super().__init__(name)
        self.strategy_name = "Always Cooperate"

    def play(self) -> Move:
        return Move.COOPERATE


class AlwaysDefectPlayer(Player):
    """Always defects"""

    def __init__(self, name=None):
        super().__init__(name)
        self.strategy_name = "Always Defect"

    def play(self) -> Move:
        return Move.DEFECT


class TitForTatPlayer(Player):
    """Cooperates on the first move, then mimics the opponent's previous move"""

    def __init__(self, name=None):
        super().__init__(name)
        self.strategy_name = "Tit For Tat"

    def play(self) -> Move:
        if len(self.game_history) == 0:
            return Move.COOPERATE
        else:
            return self.game_history[-1][1]


class RandomPlayer(Player):
    """Plays randomly"""

    def __init__(self, name=None):
        super().__init__(name)
        self.strategy_name = "Random"

    def play(self) -> Move:
        return random.choice([Move.COOPERATE, Move.DEFECT])


class DetectivePlayer(Player):
    """Plays Cooperate, Defect, Cooperate, Cooperate. If the opponent defects, plays tit for tat.
    If not, plays always defect."""

    def __init__(self, name=None):
        super().__init__(name)
        self.strategy_name = "Detective"

    def play(self) -> Move:
        if len(self.game_history) == 0:
            return Move.COOPERATE
        elif len(self.game_history) == 1:
            return Move.DEFECT
        elif len(self.game_history) == 2:
            return Move.COOPERATE
        elif len(self.game_history) == 3:
            return Move.COOPERATE
        else:
            if (
                self.game_history[-1][1] == Move.DEFECT
                or self.game_history[-2][1] == Move.DEFECT
                or self.game_history[-3][1] == Move.DEFECT
                or self.game_history[-4][1] == Move.DEFECT
            ):
                return self.game_history[-1][1]
            else:
                return Move.DEFECT


class SuspiciousTitForTatPlayer(Player):
    """Defects on the first move, then mimics the opponent's previous move. Also known as Cautious Tit for Tat."""

    def __init__(self, name=None):
        super().__init__(name)
        self.strategy_name = "Suspicious Tit For Tat"

    def play(self) -> Move:
        if len(self.game_history) == 0:
            return Move.DEFECT
        else:
            return self.game_history[-1][1]


class TitForTwoTatsPlayer(Player):
    """Cooperates unless the opponent's last two moves were defects."""

    def __init__(self, name=None):
        super().__init__(name)
        self.strategy_name = "Tit For Two Tats"

    def play(self) -> Move:
        if len(self.game_history) < 2:
            return Move.COOPERATE
        elif (
            self.game_history[-1][1] == Move.DEFECT
            and self.game_history[-2][1] == Move.DEFECT
        ):
            return Move.DEFECT
        else:
            return Move.COOPERATE


class TatForTitPlayer(Player):
    """Does the opposite of what the opponent did in the last play."""

    def __init__(self, name=None):
        super().__init__(name)
        self.strategy_name = "Tat For Tit"

    def play(self) -> Move:
        if len(self.game_history) == 0:
            return Move.COOPERATE
        else:
            return (
                Move.DEFECT
                if self.game_history[-1][1] == Move.COOPERATE
                else Move.COOPERATE
            )
