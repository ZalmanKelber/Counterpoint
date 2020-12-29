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

from fifth_species import FifthSpeciesCounterpointGenerator
from one_line import OneLine

from filter_functions.melodic_insertion_checks import end_stepwise

from filter_functions.rhythmic_insertion_filters import enforce_max_long_notes_on_downbeats

from filter_functions.change_parameter_checks import check_for_added_downbeat_long_note

class FreeMelodyGenerator (FifthSpeciesCounterpointGenerator, OneLine):
    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        self._melodic_insertion_checks.append(end_stepwise)

        self._rhythmic_insertion_filters.append(enforce_max_long_notes_on_downbeats)
    
        self._change_parameters_checks.append(check_for_added_downbeat_long_note)

    #override:
    #override the initialize function so that we can assign the max number of downbeat notes equal or longer than Whole Notes
    def _initialize(self) -> None:
        super()._initialize()
        self._assign_max_downbeat_whole_notes()

    def _assign_max_downbeat_whole_notes(self) -> None:
        self._attempt_parameters[0]["max_downbeat_long_notes"] = 0 if random() < .5 else 1
        self._attempt_parameters[0]["downbeat_long_notes_placed"] = 0

    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500 or (self._number_of_backtracks > 300 and len(self._solutions) == 0):
            return True 
        return False 