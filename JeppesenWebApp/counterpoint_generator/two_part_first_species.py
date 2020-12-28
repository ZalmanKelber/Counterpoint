from random import randint, random

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

from two_lines import TwoLines
from first_species import FirstSpeciesCounterpointGenerator
from cantus_firmus import CantusFirmusGenerator

from filter_functions.melodic_insertion_checks import end_stepwise

from filter_functions.harmonic_insertion_checks import prevents_parallel_fifths_and_octaves_simple
from filter_functions.harmonic_insertion_checks import unison_not_allowed_on_downbeat_outside_first_and_last_measure
from filter_functions.harmonic_insertion_checks import no_more_than_four_consecutive_repeated_vertical_intervals
from filter_functions.harmonic_insertion_checks import adjacent_voices_stay_within_tenth

class TwoPartFirstSpeciesGenerator (FirstSpeciesCounterpointGenerator, TwoLines):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode, cantus_firmus_index: int = 0):
        super().__init__(length, lines, mode)
        if cantus_firmus_index not in [0, 1]:
            raise Exception("invalid cantus firmus index")

        self._melodic_insertion_checks.append(end_stepwise)

        self._harmonic_insertion_checks.append(prevents_parallel_fifths_and_octaves_simple)
        self._harmonic_insertion_checks.append(unison_not_allowed_on_downbeat_outside_first_and_last_measure)
        self._harmonic_insertion_checks.append(no_more_than_four_consecutive_repeated_vertical_intervals)
        self._harmonic_insertion_checks.append(adjacent_voices_stay_within_tenth)

        #create the cantus firmus we'll use
        self._cantus_firmus_index = cantus_firmus_index
        self._cantus_firmus = None
        while self._cantus_firmus is None:
            cantus_firmus_generator = CantusFirmusGenerator(self._length, [self._lines[self._cantus_firmus_index]], self._mode)
            cantus_firmus_generator.generate_counterpoint(must_end_by_descending_step=True)
            cantus_firmus_generator.score_solutions()
            solution = cantus_firmus_generator.get_one_solution()
            self._cantus_firmus = solution[0] if solution is not None else None

    #override:
    #we should try ten attempts before we generate another Cantus Firmus
    def _exit_attempt_loop(self) -> bool:
        if len(self._solutions) >= 10 or self._number_of_attempts >= 50: 
            return True 
        return False 

    
    #override:
    #override the initialize function.  If there is no cantus firmus and line specified, generate one first
    def _initialize(self, cantus_firmus: list[RhythmicValue] = None, line: int = None) -> None:
        if cantus_firmus is None or line is None:
            cantus_firmus = self._cantus_firmus
            line = self._cantus_firmus_index
        super()._initialize(cantus_firmus=cantus_firmus, line=line)


    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500 or (len(self._solutions) == 0 and self._number_of_backtracks > 100):
            return True 
        return False 