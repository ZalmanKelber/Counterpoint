from abc import ABC

from random import randint, random, shuffle
import math

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange, Hexachord
from notation_system.mode_resolver import ModeResolver

from fifth_species import FifthSpeciesCounterpointGenerator
from one_line import OneLine

from filter_functions.melodic_insertion_checks import begin_and_end_on_mode_final
from filter_functions.melodic_insertion_checks import enforce_interval_order_strict
from filter_functions.melodic_insertion_checks import handles_interval_order_loosest
from filter_functions.melodic_insertion_checks import start_with_outline_pitch

from filter_functions.rhythmic_insertion_filters import end_on_breve
from filter_functions.rhythmic_insertion_filters import handles_rhythm_of_penultimate_measure

from filter_functions.change_parameter_checks import check_for_added_downbeat_long_note

from filter_functions.final_checks import check_for_second_outline_pitch

class ImitationThemeGenerator (FifthSpeciesCounterpointGenerator, OneLine):
    def __init__(self, length: int, lines: list[VocalRange], mode: Mode, lowest: Note, highest: Note, hexachord: Hexachord):
        super().__init__(length, lines, mode)
        self._lowest = lowest
        self._highest = highest
        self._hexachord = hexachord

        self._melodic_insertion_checks.remove(begin_and_end_on_mode_final)
        self._melodic_insertion_checks.remove(handles_interval_order_loosest)

        self._melodic_insertion_checks.append(enforce_interval_order_strict)
        self._melodic_insertion_checks.append(start_with_outline_pitch)

        self._rhythmic_insertion_filters.remove(end_on_breve)
        self._rhythmic_insertion_filters.remove(handles_rhythm_of_penultimate_measure)

        self._final_checks.append(check_for_second_outline_pitch)


    #override:
    #Dotted Whole Notes should be available for any downbeat in an opening Theme
    def _get_available_durations(self, line: int, bar: int, beat: float) -> set[int]:
        if (bar, beat) == (0, 0):
            if self._length == 3:
                return { 6 }
            else:
                return { 6, 8, 12, 16 }
        elif beat == 0:
            return { 2, 4, 6, 8, 12 }
        elif beat == 2:
            return { 2, 4, 6, 8 }
        else:
            return { 2 }

    #override:
    #in the Imitation Theme, we rely on the predetermined highest and lowest notes and do not require 
    #either to appear within the theme
    def _assign_highest_and_lowest(self) -> None:
        self._attempt_parameters[0]["lowest"] = self._lowest
        self._attempt_parameters[0]["highest"] = self._highest
        self._attempt_parameters[0]["lowest_must_appear_by"] = self._length
        self._attempt_parameters[0]["highest_must_appear_by"] = self._length

        outline_pitches = self._mode_resolver.get_outline_pitches(self._hexachord)
        shuffle(outline_pitches)

        self._attempt_parameters[0]["first_outline_pitch"] = outline_pitches[0]
        self._attempt_parameters[0]["second_outline_pitch"] = outline_pitches[1]


    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500 or (self._number_of_backtracks > 300 and len(self._solutions) == 0):
            return True 
        return False 