from random import random, randint, shuffle
import math

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

from two_part_free_counterpoint import TwoPartFreeCounterpointGenerator
from imitation_opening import ImitationOpeningGenerator


class TwoPartImitativeCounterpointGenerator (TwoPartFreeCounterpointGenerator):
    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        #decide the vocal ranges in advance using the super() version of assign highest and lowest
        self._attempt_parameters = [{}, {}]
        super()._assign_highest_and_lowest()
        self._lowest_pitches = [self._attempt_parameters[line]["lowest"] for line in range(self._height)]
        self._highest_pitches = [self._attempt_parameters[line]["highest"] for line in range(self._height)]

        #generate an imitation opening
        optimal = None
        count = 0
        while optimal is None and count < 1:
            count += 1
            imitation_opening_generator = ImitationOpeningGenerator(length, lines, mode, self._lowest_pitches, self._highest_pitches)
            imitation_opening_generator.generate_counterpoint()
            imitation_opening_generator.score_solutions()
            optimal = imitation_opening_generator.get_one_solution()
        self._opening = optimal
        self._opening_bars = self._get_number_of_bars(optimal) if optimal is not None else 0

    #override:
    #if we haven't generated an opening, don't run the loop
    def generate_counterpoint(self) -> None:
        if self._opening is None:
            return 
        self._number_of_attempts = 0
        while not self._exit_attempt_loop():
            self._number_of_attempts += 1
            self._initialize()
            self._backtrack()
            print("highest index reached:", self._highest_index_reached)
        print("number of solutions:", len(self._solutions),"number of attempts:", self._number_of_attempts, "number of backtracks:", self._number_of_backtracks)
        return 

    #override:
    #since our range is already decided during the initialization, we can use the values we generated
    def _assign_highest_and_lowest(self) -> None:
        for line in range(self._height):
            self._attempt_parameters[line]["lowest"] = self._lowest_pitches[line]
            self._attempt_parameters[line]["highest"] = self._highest_pitches[line]
            if self._length - 1 >= self._opening_bars + 2:
                self._attempt_parameters[line]["lowest_must_appear_by"] = randint(self._opening_bars + 2, self._length - 1) 
                self._attempt_parameters[line]["highest_must_appear_by"] = randint(self._opening_bars + 2, self._length - 1)
            else:
                self._attempt_parameters[line]["lowest_must_appear_by"] = self._length - 1
                self._attempt_parameters[line]["highest_must_appear_by"] = self._length - 1

    #override:
    #map the opening onto the stack and determine if the highest notes have been placed 
    def _initialize(self) -> None:
        super()._initialize()
        for line in range(self._height):
            for entity in self._opening[line]:
                if isinstance(entity, Pitch):
                    if entity.is_unison(self._attempt_parameters[line]["lowest"]):
                        self._attempt_parameters[line]["lowest_has_been_placed"] = True 
                    if entity.is_unison(self._attempt_parameters[line]["highest"]):
                        self._attempt_parameters[line]["highest_has_been_placed"] = True 
            self.assign_melody_to_line(self._opening[line], line)

    #override:
    #ensure that suspension bars don't overlap with opening
    def _assign_suspension_bars(self) -> None:
        min_num_suspensions = randint(1, 2) if self._length - self._opening_bars > 5 else 1
        suspension_bars = [self._length - 2]
        for i in range(min_num_suspensions - 1):
            suspension_bar = randint(self._opening_bars + 1, self._length - 3)
            while suspension_bar in suspension_bars:
                suspension_bar = randint(self._opening_bars + 1, self._length - 3)
            suspension_bars.append(suspension_bar)
        for line in range(2):
            self._attempt_parameters[line]["suspension_bars"] = []
        for suspension_bar in suspension_bars:
            if random() < .33:
                self._attempt_parameters[0]["suspension_bars"].append(suspension_bar)
            else:
                self._attempt_parameters[1]["suspension_bars"].append(suspension_bar)


    #determine the number of bars taken up by the opening
    def _get_number_of_bars(self, opening: list[list[RhythmicValue]]) -> int:
        for line in range(self._height):
            if isinstance(opening[line][0], Rest):
                total_duration = 0
                for entity in opening[line]:
                    total_duration += entity.get_duration()
                return math.ceil(total_duration / 8)

    #override:
    #exit the attempt loop after ten attempts
    def _exit_attempt_loop(self) -> bool:
        return len(self._solutions) >= 100 or self._number_of_attempts >= 20 or (self._number_of_attempts >= 10 and len(self._solutions) > 0)
