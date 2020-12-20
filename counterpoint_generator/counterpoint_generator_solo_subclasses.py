import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from random import random

from abc import ABC

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from mode_resolver import ModeResolver

from counterpoint_generator import CounterpointGenerator

from counterpoint_generator_species_subclasses import FirstSpeciesCounterpointGenerator
from counterpoint_generator_species_subclasses import FifthSpeciesCounterpointGenerator
from counterpoint_generator_subclasses import SoloMelody

from filter_functions.melodic_insertion_checks import last_interval_is_descending_step
from filter_functions.melodic_insertion_checks import end_stepwise

from filter_functions.rhythmic_insertion_filters import enforce_max_long_notes_on_downbeats

from filter_functions.change_parameter_checks import check_for_added_downbeat_long_note

class CantusFirmusGenerator (FirstSpeciesCounterpointGenerator, SoloMelody):

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

class FreeMelodyGenerator (FifthSpeciesCounterpointGenerator, SoloMelody):
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