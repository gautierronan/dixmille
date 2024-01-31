import random
from collections import namedtuple

GameState = namedtuple('GameState', ['scores', 'dice_values', 'dice_locked', 'pid'])

class DiceGameEnv:
    def __init__(self, num_players=5, num_dice=5):
        self.num_players = num_players
        self.num_dice = num_dice
        self.reset()

    def reset(self):
        self.scores = [0] * self.num_players
        self.dice_values = self._roll_dice(self.num_dice) # [2 5 3 1 2]
        self.dice_locked = [False] * self.num_dice # [F F F F F]
        self.running_score = 0 # update with running score
        self.turn_start = False
        self.pid = 0
        return self._get_state()

    def _get_state(self):
        return self.scores, self.running_score, self.dice_values, self.dice_locked, self.pid

    def _roll_dice(self, num_dice):
        return [random.randint(1, 6) for _ in range(num_dice)]

    def step(self, dice_to_reroll):
        # [T T T T T]: full reroll at turn start
        if all(dice_to_reroll) and self.turn_start:
            self.dice_values = self._roll_dice(self.num_dice)
            self.dice_locked = [False] * self.num_dice
            self.turn_start = False
            return self._get_state(), 0, False, {}

        dice_to_reroll = [not locked and reroll for locked, reroll in zip(self.dice_locked, dice_to_reroll)]

        # [F F F F F] and turn_start: illegal move -> force full reroll
        if not any(dice_to_reroll) and self.turn_start:
            self.dice_values = self._roll_dice(self.num_dice)
            self.dice_locked = [False] * self.num_dice
            self.turn_start = False
            return self._get_state(), 0, False, {}

        # [F F F F F] and not turn_start: redeem score
        if not any(dice_to_reroll) and not self.turn_start:
            pass

        # lock dice that are not rerolled
        self.dice_locked = [locked or not reroll for locked, reroll in zip(self.dice_locked, dice_to_reroll)]

        # reroll dice that are rerolled
        self.dice_values = [random.randint(1, 6) if reroll else value for value, reroll in zip(self.dice_values, dice_to_reroll)]


        return self._get_state(), score, done, {}

    def render(self):
        print(f"Dice Values: {self.dice_values}")
        print(f"Dice Locked: {self.dice_locked}")
        for i, score in enumerate(self.scores):
            print(f"Player {i+1}'s score: {score}")

# Example of using the environment
env = DiceGameEnv()
state = env.reset()
done = False

while not done:
    action = [random.choice([True, False]) for _ in range(env.num_dice)]
    state, reward, done, _ = env.step(action)
    env.render()
