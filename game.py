import numpy.random as random
import numpy as np


def find_equal_to(arr, n):
    mask = arr == arr[n]
    mask[n] = False
    return np.where(mask)[0]


class DixMilleAI:
    def __init__(self, num_players):
        self.num_players = num_players
        self.scores = np.array([0] * num_players)
        self.winner = None

    def play(self):
        pid = 0
        running_score = 0
        num_dice = 5
        while True:
            # roll the dice
            roll = random.randint(1, 6, num_dice)
            score, num_scoring = self.get_score(roll)
            self.print_roll(pid, roll)

            # main pleine: replay with 5 dice
            if num_scoring == num_dice:
                num_dice = 5
                running_score += score
                self.print_main_pleine(pid, score)
                continue
            # did not score: go to next player with dice reset
            elif num_scoring == 0:
                num_dice = 5
                running_score = 0

                # go to next player
                self.print_scoring(pid, running_score)
                pid = self.next_player(pid)
                self.print_new_player(pid)
            # scored
            else:
                # decide which dice to remove
                score_with = score
                for idx in range(len(roll) - 1, -1, -1):
                    roll_without = np.delete(roll, idx)
                    score_without, num_scoring_without = self.get_score(roll_without)
                    if num_scoring_without > 0 and self.decide_to_remove_dice(
                        score_without, score_with
                    ):
                        roll = roll_without
                        score = score_without
                        score_with = score_without
                        num_scoring = num_scoring_without
                self.print_subroll(pid, roll, score)

                # update running score
                running_score += score
                num_dice -= num_scoring

                # if player score is equal to 10000: we have a winner
                if self.scores[pid] + running_score == 10_000:
                    self.scores[pid] += running_score
                    self.winner = pid
                    return
                # if player score is over 10000: go to next player
                elif self.scores[pid] + running_score > 10_000:
                    # go to next player
                    self.print_scoring(pid, running_score)
                    pid = self.next_player(pid)
                    self.print_new_player(pid)

                    # check if next player wants to reset or not
                    if self.decide_to_reset(running_score, num_dice):
                        running_score = 0
                        num_dice = 5
                # decide to redeem runnning score or not
                elif self.decide_to_redeem(running_score, num_dice):
                    # score
                    self.scores[pid] += running_score
                    self.print_scoring(pid, running_score)

                    # check if another player gets eaten
                    equal_pids = find_equal_to(self.scores, pid)
                    if len(equal_pids) > 0:
                        for equal_pid in equal_pids:
                            self.print_eat(pid, equal_pid)
                            self.scores[equal_pid] = (
                                0 if self.scores[equal_pid] <= 5_000 else 5_000
                            )

                    # go to next player
                    pid = self.next_player(pid)
                    self.print_new_player(pid)

                    # check if next player wants to reset or not
                    if self.decide_to_reset(running_score, num_dice):
                        running_score = 0
                        num_dice = 5

    def next_player(self, pid):
        return (pid + 1) % self.num_players

    def get_score(self, roll):
        values, counts = np.unique(roll, return_counts=True)
        score = 0
        num_scoring = 0
        if len(values) == 5:
            score += 500
            num_scoring += 5
        else:
            for value, count in zip(values, counts):
                if count == 5:
                    score += 10_000
                    num_scoring += 5
                elif count == 4:
                    if value == 1:
                        score += 2_000
                    else:
                        score += 1_000
                    num_scoring += 4
                elif count == 3:
                    if value == 1:
                        score += 1_000
                    else:
                        score += value * 100
                    num_scoring += 3
                elif value == 1:
                    score += 100 * count
                    num_scoring += count
                elif value == 5:
                    score += 50 * count
                    num_scoring += count

        return score, num_scoring

    def decide_to_redeem(self, running_score, num_dice):
        if running_score >= 1000:
            return True
        elif running_score >= 750 and num_dice <= 3:
            return True
        elif running_score >= 500 and num_dice <= 2:
            return True
        elif running_score >= 250 and num_dice == 1:
            return True
        else:
            return False

    def decide_to_reset(self, running_score, num_dice):
        if running_score >= 500 and num_dice >= 2:
            return False
        elif running_score >= 800 and num_dice >= 1:
            return False
        else:
            return True

    def decide_to_remove_dice(self, score_without, score_with):
        if score_with - score_without <= 50:
            return True
        else:
            return False

    def print_new_player(self, pid):
        print(f"============================")
        print(f"Player {pid} is now playing.")

    def print_roll(self, pid, roll):
        print(f"Player {pid} rolled {roll}.")

    def print_subroll(self, pid, roll, score):
        print(f"Player {pid} kept {roll} for {score} points.")

    def print_main_pleine(self, pid, score):
        print(f"Player {pid} got a main pleine for {score} points.")

    def print_scoring(self, pid, score):
        print(
            f"Player {pid} scored {score} points and now has {self.scores[pid]} points."
        )

    def print_eat(self, pid, equal_pid):
        print(f"Player {pid} ate player {equal_pid}.")


dixmille = DixMilleAI(5)
dixmille.play()
print(dixmille.scores)
print(dixmille.winner)
