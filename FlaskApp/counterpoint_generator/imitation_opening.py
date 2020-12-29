from random import random, randint, shuffle
import math

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange, Hexachord
from notation_system.mode_resolver import ModeResolver

from two_part_free_counterpoint import TwoPartFreeCounterpointGenerator
from imitation_theme import ImitationThemeGenerator

from filter_functions.melodic_insertion_checks import begin_and_end_two_part_counterpoint
from filter_functions.melodic_insertion_checks import follow_imitation_pattern

from filter_functions.harmonic_insertion_checks import start_and_end_intervals_two_part

from filter_functions.rhythmic_insertion_filters import follow_imitation_pattern_rhythm

from filter_functions.score_functions import penalize_rests

class ImitationOpeningGenerator (TwoPartFreeCounterpointGenerator):
    def __init__(self, length: int, lines: list[VocalRange], mode: Mode, lowest_pitches: list[Pitch], highest_pitches: list[Pitch]):
        super().__init__(length, lines, mode)
        self._lowest_pitches = lowest_pitches
        self._highest_pitches = highest_pitches
        self._imitation_bars = randint(3, 6) if length > 14 else randint(3, 5)

        self._melodic_insertion_checks.remove(begin_and_end_two_part_counterpoint)

        self._melodic_insertion_checks.append(follow_imitation_pattern)

        self._harmonic_insertion_checks.remove(start_and_end_intervals_two_part)

        self._rhythmic_insertion_filters.append(follow_imitation_pattern_rhythm)

        self._score_functions.append(penalize_rests)

    #override:
    #in the Imitation Opening, we rely on the predetermined highest and lowest notes and do not require 
    #either to appear within the theme
    #we also need to clear the suspension bars parameter
    def _assign_highest_and_lowest(self) -> None:
        for line in range(self._height):
            self._attempt_parameters[line]["lowest"] = self._lowest_pitches[line]
            self._attempt_parameters[line]["highest"] = self._highest_pitches[line]
            self._attempt_parameters[line]["lowest_must_appear_by"] = self._length
            self._attempt_parameters[line]["highest_must_appear_by"] = self._length

    #override:
    #after initialization, choose one line to have an imitative theme and calculate the interval difference 
    def _initialize(self) -> None:
        super()._initialize()
        self._starting_line = 0 if random() < .5 else 1
        self._starting_hexachord = Hexachord.DURUM if random() < .5 else Hexachord.MOLLE
        if self._starting_line == 0 and self._starting_hexachord == Hexachord.DURUM:
            self._translation_interval = 4
        if self._starting_line == 0 and self._starting_hexachord == Hexachord.MOLLE:
            self._translation_interval = 5
        if self._starting_line == 1 and self._starting_hexachord == Hexachord.DURUM:
            self._translation_interval = -5
        if self._starting_line == 1 and self._starting_hexachord == Hexachord.MOLLE:
            self._translation_interval = -4

        #generate the Imitative Theme
        lines = [self._lines[self._starting_line]]
        lowest = self._attempt_parameters[self._starting_line]["lowest"]
        highest = self._attempt_parameters[self._starting_line]["highest"]
        hexachord = self._starting_hexachord
        optimal = None
        # print("highest", highest, "lowest", lowest, "hexachord", hexachord, "lines", lines)
        count = 0
        while optimal is None and count < 20:
            count += 1
            theme_generator = ImitationThemeGenerator(self._imitation_bars, lines, self._mode, lowest, highest, hexachord)
            theme_generator.generate_counterpoint()
            theme_generator.score_solutions()
            optimal = theme_generator.get_one_solution()
        # print("found theme")
        if optimal is None:
            return
        self.assign_melody_to_line(optimal[0], self._starting_line)
        self._remaining_indices[self._starting_line] = []

        for line in range(self._height):
            self._attempt_parameters[line]["suspension_bars"] = []

    #override:
    #if there is no imitative theme, exit the loop
    def _backtrack(self) -> None:
        if len(self._remaining_indices[self._starting_line]) > 0:
            return
        super()._backtrack()

    #override:
    #change the conditions of the reached possible solution function to return true if we've finished the imitation
    def _reached_possible_solution(self) -> bool:
        imitation_length = len(self._counterpoint_stacks[self._starting_line])
        other_length = len(self._counterpoint_stacks[(self._starting_line + 1) % 2])
        num_rests = self._attempt_parameters[(self._starting_line + 1) % 2]["number_of_rests"]
        if other_length - num_rests == imitation_length: 
            return True 
        return False

    #override:
    #allow all possible rhythmic durations and let the filter remove ineligible durations
    def _get_available_durations(self, line: int, bar: int, beat: float) -> set[int]:
        return { 2, 4, 6, 8, 12, 16 }

    #override:
    #Whole Note Rests are available as long as we haven't placed any Notes yet
    def _get_valid_rest_durations(self, line: int, bar: int, beat: float) -> set[int]:
        if len(self._counterpoint_stacks[line]) == 0 or isinstance(self._counterpoint_stacks[line][-1], Rest):
            c_note = self._get_counterpoint_pitch(self._starting_line, bar, beat) 
            if c_note is not None:
                return { 8 }
        return set()

    #override:
    #exit the attempt loop once a solution is found
    def _exit_attempt_loop(self) -> bool:
        return len(self._solutions) >= 100 or self._number_of_attempts >= 5