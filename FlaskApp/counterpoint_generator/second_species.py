from abc import ABC

from random import randint, random, shuffle
import math

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

from base_class import CounterpointGenerator

from filter_functions.melodic_insertion_checks import prevent_cross_relations_on_notes_separated_by_one_other_note
from filter_functions.melodic_insertion_checks import enforce_interval_order_strict
from filter_functions.melodic_insertion_checks import prevent_dissonances_from_being_outlined
from filter_functions.melodic_insertion_checks import prevent_any_repetition_of_three_intervals
from filter_functions.melodic_insertion_checks import prevent_highest_note_from_being_in_middle
from filter_functions.melodic_insertion_checks import melody_cannot_change_direction_three_times_in_a_row
from filter_functions.melodic_insertion_checks import prevent_three_notes_from_immediately_repeating
from filter_functions.melodic_insertion_checks import pitch_cannot_appear_three_times_in_six_notes
from filter_functions.melodic_insertion_checks import end_stepwise
from filter_functions.melodic_insertion_checks import prevents_repetition_second_species
from filter_functions.melodic_insertion_checks import sharp_notes_resolve_upwards
from filter_functions.melodic_insertion_checks import prevents_fifteenth_century_sharp_resolution


from filter_functions.final_checks import ascending_intervals_are_filled_in


class SecondSpeciesCounterpointGenerator (CounterpointGenerator, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        self._melodic_insertion_checks.append(prevent_cross_relations_on_notes_separated_by_one_other_note)
        self._melodic_insertion_checks.append(enforce_interval_order_strict)
        self._melodic_insertion_checks.append(prevent_dissonances_from_being_outlined)
        self._melodic_insertion_checks.append(prevent_any_repetition_of_three_intervals)
        self._melodic_insertion_checks.append(prevent_highest_note_from_being_in_middle)
        self._melodic_insertion_checks.append(end_stepwise)
        self._melodic_insertion_checks.append(sharp_notes_resolve_upwards)
        self._melodic_insertion_checks.append(melody_cannot_change_direction_three_times_in_a_row)
        self._melodic_insertion_checks.append(prevent_three_notes_from_immediately_repeating)
        self._melodic_insertion_checks.append(pitch_cannot_appear_three_times_in_six_notes)
        self._melodic_insertion_checks.append(prevents_repetition_second_species)
        self._melodic_insertion_checks.append(prevents_fifteenth_century_sharp_resolution)

        self._final_checks.append(ascending_intervals_are_filled_in)

    #override:
    #override the get_available_durations, which consists entirely of Half Notes in the Second Speices except the penultimate measure
    #note that we rely on the base class for the _get_valid_rests method
    def _get_available_durations(self, line: int, bar: int, beat: float) -> set[int]:
        if bar == self._length - 1:
            return { 16 }
        elif (bar, beat) == (self._length - 2, 0):
            return { 4, 8}
        else:
            return { 4 }


    #override:
    #override the function that assigns the highest and lowest intervals
    #a First Species exercise should have a range between a fifth and octave, should include
    #the mode final on a note that is not the highest pitch, and the lowest and highest note should not form a diminished fifth 
    def _assign_highest_and_lowest(self) -> None:
        for line in range(self._height):
            vocal_range = self._lines[line]
            #choose a range interval between a seventh and tenth and choose a highest and lowest note
            range_size = randint(7, 10)
            range_bottom = self._mode_resolver.get_lowest_of_range(vocal_range)

            self._attempt_parameters[line]["lowest"] = self._mode_resolver.get_default_pitch_from_interval(range_bottom, randint(1, 13 - range_size))
            self._attempt_parameters[line]["highest"] = self._mode_resolver.get_default_pitch_from_interval(self._attempt_parameters[line]["lowest"], range_size)

            self._attempt_parameters[line]["lowest_must_appear_by"] = randint(3, self._length - 1)
            self._attempt_parameters[line]["highest_must_appear_by"] = randint(3, self._length - 1)

