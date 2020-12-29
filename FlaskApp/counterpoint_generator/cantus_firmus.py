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

from first_species import FirstSpeciesCounterpointGenerator
from one_line import OneLine

from filter_functions.melodic_insertion_checks import last_interval_is_descending_step

class CantusFirmusGenerator (FirstSpeciesCounterpointGenerator, OneLine):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        #Add the end by descending step optional function
        self._melodic_insertion_checks.append(last_interval_is_descending_step)
    
    #override:
    #override the generate counterpoint function to provide the option of ending by descending step
    def generate_counterpoint(self, must_end_by_descending_step: bool = False) -> None:
        #this property is referenced by the last_interval_is_descending_step insertion check to determine whether 
        #or not to enforce the rule
        self._must_end_by_descending_step = must_end_by_descending_step
        super().generate_counterpoint()

    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500:
            return True 
        return False 
