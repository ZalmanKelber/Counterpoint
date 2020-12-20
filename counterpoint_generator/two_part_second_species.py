import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from random import randint, random

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from mode_resolver import ModeResolver

from counterpoint_generator_subclasses import TwoPartCounterpoint
from counterpoint_generator_species_subclasses import SecondSpeciesCounterpointGenerator
from counterpoint_generator_solo_subclasses import CantusFirmusGenerator


from filter_functions.harmonic_insertion_checks import unison_not_allowed_on_downbeat_outside_first_and_last_measure
from filter_functions.harmonic_insertion_checks import adjacent_voices_stay_within_tenth
from filter_functions.harmonic_insertion_checks import forms_passing_tone_second_species
from filter_functions.harmonic_insertion_checks import resolves_passing_tone_second_species
from filter_functions.harmonic_insertion_checks import prevents_parallel_fifths_and_octaves_simple

class TwoPartSecondSpeciesGenerator (SecondSpeciesCounterpointGenerator, TwoPartCounterpoint):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode, cantus_firmus_index: int = 0):
        super().__init__(length, lines, mode)
        if cantus_firmus_index not in [0, 1]:
            raise Exception("invalid cantus firmus index")

        self._harmonic_insertion_checks.append(unison_not_allowed_on_downbeat_outside_first_and_last_measure)
        self._harmonic_insertion_checks.append(adjacent_voices_stay_within_tenth)
        self._harmonic_insertion_checks.append(forms_passing_tone_second_species)
        self._harmonic_insertion_checks.append(resolves_passing_tone_second_species)
        self._harmonic_insertion_checks.append(prevents_parallel_fifths_and_octaves_simple)

        #create the cantus firmus we'll use
        self._cantus_firmus_index = cantus_firmus_index
        self._cantus_firmus = None
        while self._cantus_firmus is None:
            cantus_firmus_generator = CantusFirmusGenerator(self._length, [self._lines[self._cantus_firmus_index]], self._mode)
            cantus_firmus_generator.generate_counterpoint(must_end_by_descending_step=True if self._cantus_firmus_index == 1 else False)
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