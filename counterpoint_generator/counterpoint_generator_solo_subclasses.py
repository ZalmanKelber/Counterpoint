import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from abc import ABC

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from mode_resolver import ModeResolver

from counterpoint_generator import CounterpointGenerator

from counterpoint_generator_species_subclasses import FirstSpeciesCounterpointGenerator
from counterpoint_generator_subclasses import SoloMelody

from filter_functions.melodic_insertion_checks import last_interval_is_descending_step

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
        print("number of backtracks:", self._number_of_backtracks)

    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500:
            return True 
        return False 
