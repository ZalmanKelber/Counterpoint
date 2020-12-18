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

#favorably scores Fifth Species examples with long Quarter Note runs
def prioritize_long_quarter_note_runs(self: object) -> int:
    score_add_on = 0
    for line in range(self._height):
        max_run_length = 0
        current_run_length = 0
        for i, entity in enumerate(self._counterpoint_stacks[line]):
            if isinstance(entity, Pitch) and entity.get_duration() <= 2:
                if i == 0 or not isinstance(self._counterpoint_stacks[line][i - 1], Pitch) or self._counterpoint_stacks[line][i - 1].get_duration() > 2:
                    current_run_length = 1
                else:
                    current_run_length += 1
                if current_run_length > max_run_length:
                    max_run_length = current_run_length
        if max_run_length > 4:
            score_add_on -= 20 * (max_run_length - 4)
        else:
            score_add_on += 30 * (4 - max_run_length)
    return score_add_on

#favorably scores Fifth Species examples without Quarter Note runs of length 2
def penalize_two_note_quarter_runs(self: object) -> int:
    score_add_on = 0
    for line in range(self._height):
        for i in range(3, len(self._counterpoint_stacks[line])):
            if ( isinstance(self._counterpoint_stacks[line][i - 3], Pitch) and self._counterpoint_stacks[line][i - 3].get_duration() > 2
                and self._counterpoint_stacks[line][i - 2].get_duration() == 2 and self._counterpoint_stacks[line][i - 1].get_duration() == 2
                and self._counterpoint_stacks[line][i].get_duration() > 2 ):
                score_add_on += 15
    return score_add_on
            
def select_ideal_ties(self: object) -> int:
    score_add_on = 0
    for line in range(self._height):
        num_ties = 0
        num_tied_dotted_halfs = 0
        num_tied_wholes = 0
        ties = [False] * (self._length - 2)
        for i in range(1, self._length - 1):
            if (i, 0) not in self._counterpoint_objects[line]: 
                ties[i - 1] = True
                num_ties += 1
                if (i - 1, 2) in self._counterpoint_objects[line] and isinstance(self._counterpoint_objects[line][(i - 1, 2)], Pitch):
                    if self._counterpoint_objects[line][(i - 1, 2)].get_duration() == 6:
                        num_tied_dotted_halfs += 1
                    else:
                        num_tied_wholes += 1
        ideal_ties = 3 if self._length < 12 else 4 
        score_add_on += abs(ideal_ties - num_ties) * 10 
        score_add_on += abs(num_tied_wholes - num_tied_dotted_halfs) * 7
        has_isolated_tie = False
        for i in range(1, len(ties) - 1):
            if ties[i - 1] == False and ties[i] == True and ties[i + 1] == False:
                has_isolated_tie = True 
        if has_isolated_tie: 
            score_add_on += 12
    return score_add_on
        


