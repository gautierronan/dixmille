import random
from collections import namedtuple
import numpy as np


def flatten(lst):
    """Flatten a list of ints and lists."""
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten(i))
        else:
            result.append(i)
    return result

def find_equal_to(arr, n):
    indices = []
    for i, value in enumerate(arr):
        if value == arr[n] and i != n:
            indices.append(i)
    return indices

class DiceGameEnv:
    def __init__(self, num_players=5, num_dice=5, verbose=True):
        self.num_players = num_players
        self.num_dice = num_dice
        self.verbose = verbose
        self.reset()

    def reset(self):
        self.scores = [0] * self.num_players
        self.running_score = 0
        self.num_dice_available = self.num_dice
        self.turn_start = False
        self.pid = 0
        self._print_new_player(self.pid)
        self._roll_until_decision()
        return self._get_state()

    def _get_state(self):
        return self.scores, self.running_score, self.num_dice_available, self.turn_start, self.pid, self.dice_available

    def _roll_dice(self, num_dice):
        return [random.randint(1, 6) for _ in range(num_dice)]

    def _roll_until_decision(self):
        # roll all available dice
        while True:
            roll = self._roll_dice(self.num_dice_available)
            subroll, score, num_scoring = self._get_score(roll)
            self._print_roll(self.pid, roll)
            if num_scoring == self.num_dice_available:
                # player full rerolls
                self._print_main_pleine(self.pid, score)
                self.running_score += score
                self.num_dice_available = self.num_dice
                self.turn_start = False
            elif num_scoring == 0:
                # go to next player
                self.running_score = 0
                self._print_scoring(self.pid, self.running_score)
                self.num_dice_available = self.num_dice
                self.turn_start = True
                self.pid = self._next_player(self.pid)
                self._print_new_player(self.pid)
            elif self.scores[self.pid] + self.running_score + score > 10_000:
                # go to next player and decision point
                self._print_over_10k(self.pid, self.scores[self.pid] + self.running_score + score)
                self.turn_start = True
                self.pid = self._next_player(self.pid)
                self._print_new_player(self.pid)
                break
            else:
                # decision point
                self.turn_start = False
                break

        self.dice_available = subroll
        self.score_available = score

    def _next_player(self, pid):
        return (pid + 1) % self.num_players

    def _get_score(self, roll):
        # [4, 4, 4, 3, 1]
        # -> [[4, 4, 4], 1], 500, 4
        # [5, 5, 5, 5, 2]
        # -> [5, 5, 5, 5], 1000, 4
        values, counts = np.unique(flatten(roll), return_counts=True)
        subroll = []
        score = 0
        num_scoring = 0
        if len(values) == 5:
            subroll = roll
            score += 500
            num_scoring += 5
        else:
            for value, count in zip(values, counts):
                if count == 5:
                    subroll += [value] * 5 if value in [1, 5] else [[value] * 5]
                    score += 10_000
                    num_scoring += 5
                elif count == 4:
                    if value == 1:
                        score += 2_000
                    else:
                        score += 1_000
                    subroll += [value] * 4 if value in [1, 5] else [[value] * 4]
                    num_scoring += 4
                elif count == 3:
                    if value == 1:
                        score += 1_000
                    else:
                        score += value * 100
                    subroll += [value] * 3 if value in [1, 5] else [[value] * 3]
                    num_scoring += 3
                elif value == 1:
                    subroll += [value] * count
                    score += 100 * count
                    num_scoring += count
                elif value == 5:
                    subroll += [value] * count
                    score += 50 * count
                    num_scoring += count

        return subroll, score, num_scoring

    def step(self, actions):
        """
        (1) Turn start
        * player full rerolls -> actions[0] == True
        * player rerolls all available dice -> actions[0] == False
        (2) Turn ongoing (with N available dice)
        * player redeems his score -> actions[:N] == [False] * N
        * player rerolls a subset of dice -> actions[:N] == [True or False] * N
        """
        if self.turn_start:
            if actions[0]:
                # player full rerolls
                self._print_full_reroll(self.pid)
                self.running_score = 0
                self.num_dice_available = self.num_dice
                self._roll_until_decision()
            else:
                # player rerolls all available dice
                self._print_partial_reroll(self.pid, self.num_dice_available, self.running_score)
                self._roll_until_decision()
        else:
            num_can_reroll = len(self.dice_available)
            if not any(actions[:num_can_reroll]):
                # player redeems score
                subroll, score, num_scoring = self._get_score(self.dice_available)
                self.running_score += score
                self.num_dice_available = self.num_dice_available - num_scoring
                self.scores[self.pid] += self.running_score
                self._print_subroll(self.pid, subroll, score)
                self._print_scoring(self.pid, self.running_score)

                # check if player won
                if self.scores[self.pid] == 10_000:
                    return self._get_state(), 1, True, {}

                # check if another player gets eaten
                equal_pids = find_equal_to(self.scores, self.pid)
                if len(equal_pids) > 0 and self.scores[self.pid] != 0:
                    for equal_pid in equal_pids:
                        self._print_eat(self.pid, equal_pid)
                        self.scores[equal_pid] = (
                            0 if self.scores[equal_pid] <= 5_000 else 5_000
                        )

                # go to next player
                self.turn_start = True
                self.pid = self._next_player(self.pid)
                self._print_new_player(self.pid)
            else:
                # player rerolls available dice according to actions[:self.num_dice]
                subroll_to_keep = [dice for dice, flag in zip(self.dice_available, actions[:num_can_reroll]) if flag]
                subroll, score, num_scoring = self._get_score(subroll_to_keep)
                self.num_dice_available = self.num_dice_available - num_scoring
                self.running_score += score
                self._print_subroll(self.pid, subroll_to_keep, score)
                self._roll_until_decision()

        # keep playing until next decision point
        return self._get_state(), 0, False, {}

    def render(self):
        print(f"Scores: {self.scores}")
        print(f"Running Score: {self.running_score}")
        print(f"Number of dice available: {self.num_dice_available}")
        print(f"Player {self.pid}'s turn")
        print(f"Available dice: {self.dice_available}")

    def _print_new_player(self, pid):
        if self.verbose:
            print(f"============================")
            print(f"Player {pid} is now playing.")

    def _print_roll(self, pid, roll):
        if self.verbose:
            print(f"Player {pid} rolled {roll}.")

    def _print_scoring(self, pid, score):
        if self.verbose:
            print(
                f"Player {pid} scored {score} points and now has {self.scores[pid]} points."
            )

    def _print_main_pleine(self, pid, score):
        if self.verbose:
            print(f"Player {pid} got a main pleine for {score} points.")

    def _print_over_10k(self, pid, score):
        if self.verbose:
            print(f"Player {pid} has gone over 10,000 points with {score} points.")

    def _print_subroll(self, pid, subroll, subroll_score):
        if self.verbose:
            print(
                f"Player {pid} kept {flatten(subroll)} for {subroll_score} points."
            )

    def _print_eat(self, pid, equal_pid):
        if self.verbose:
            print(f"Player {pid} ate player {equal_pid}.")

    def _print_full_reroll(self, pid):
        if self.verbose:
            print(f"Player {pid} is rerolling all available dice.")

    def _print_partial_reroll(self, pid, num_dice, running_score):
        if self.verbose:
            print(f"Player {pid} is rerolling {num_dice} dice with {running_score} points.")

# Example of using the environment
env = DiceGameEnv()
done = False

while not done:
    action = [random.choice([True, False]) for _ in range(env.num_dice)]
    state, reward, done, _ = env.step(action)

print(env.scores)
