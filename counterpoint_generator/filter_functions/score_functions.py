import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

import math

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange

#an ideal melody will have ~71% of its intervals as steps
#note that we don't score the lowest voice in a three or more part example
def prioritize_stepwise_motion(self: object) -> int:
    IDEAL_STEP_RATIO = .712
    score_add_on = 0
    for line in range(0 if self._height <= 2 else 1, self._height):
        num_steps, num_intervals = 0, 0
        for i in range(len(self._counterpoint_stacks[line]) - 1):
            if isinstance(self._counterpoint_stacks[line][i], Pitch):
                num_intervals += 1
                if abs(self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1])) == 2:
                    num_steps += 1
        #add a point for every percentage point below the ideal our ratio is
        if num_steps / num_intervals < IDEAL_STEP_RATIO:
            score_add_on += math.floor((IDEAL_STEP_RATIO - (num_steps / num_intervals)) * 100)
        #add .5 points for every percentage point over the ideal our ratio is
        if num_steps / num_intervals > IDEAL_STEP_RATIO:
            score_add_on += math.floor(((num_steps / num_intervals) - IDEAL_STEP_RATIO) * 50)
    return score_add_on

#we want is many ascending leaps as possible to be followed by a descending step
def ascending_leaps_followed_by_descending_steps(self: object) -> int:
    score_add_on = 0
    for line in range(0 if self._height <= 2 else 1, self._height):
         for i, entity in enumerate(self._counterpoint_stacks[line]):
            if isinstance(entity, Pitch) and i < len(self._counterpoint_stacks[line]) - 2:
                first_interval = self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1])
                second_interval = self._counterpoint_stacks[line][i + 1].get_tonal_interval(self._counterpoint_stacks[line][i + 2])
                if first_interval > 2 and second_interval != -2:
                    score_add_on += 20
    return score_add_on

