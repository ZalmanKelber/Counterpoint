from random import randint, random

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

from two_lines import TwoLines
from third_species import ThirdSpeciesCounterpointGenerator
from cantus_firmus import CantusFirmusGenerator


from filter_functions.harmonic_insertion_checks import unison_not_allowed_on_downbeat_outside_first_and_last_measure
from filter_functions.harmonic_insertion_checks import adjacent_voices_stay_within_twelth
from filter_functions.harmonic_insertion_checks import forms_passing_tone_second_species
from filter_functions.harmonic_insertion_checks import resolves_passing_tone_second_species
from filter_functions.harmonic_insertion_checks import prevents_parallel_fifths_and_octaves_simple
from filter_functions.harmonic_insertion_checks import forms_weak_quarter_beat_dissonance
from filter_functions.harmonic_insertion_checks import resolves_weak_quarter_beat_dissonance_third_species
from filter_functions.harmonic_insertion_checks import resolves_cambiata_tail
from filter_functions.harmonic_insertion_checks import strong_quarter_beats_are_consonant

from filter_functions.score_functions import find_longest_sequence_of_steps
from filter_functions.score_functions import penalize_whole_note_in_penultimate_bar

class TwoPartThirdSpeciesGenerator (ThirdSpeciesCounterpointGenerator, TwoLines):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode, cantus_firmus_index: int = 0):
        super().__init__(length, lines, mode)
        if cantus_firmus_index not in [0, 1]:
            raise Exception("invalid cantus firmus index")

        self._harmonic_insertion_checks.append(unison_not_allowed_on_downbeat_outside_first_and_last_measure)
        self._harmonic_insertion_checks.append(adjacent_voices_stay_within_twelth)
        self._harmonic_insertion_checks.append(prevents_parallel_fifths_and_octaves_simple)
        self._harmonic_insertion_checks.append(forms_weak_quarter_beat_dissonance)
        self._harmonic_insertion_checks.append(resolves_weak_quarter_beat_dissonance_third_species)
        self._harmonic_insertion_checks.append(resolves_cambiata_tail)
        self._harmonic_insertion_checks.append(strong_quarter_beats_are_consonant)

        self._score_functions.append(find_longest_sequence_of_steps)
        self._score_functions.append(penalize_whole_note_in_penultimate_bar)

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
        return len(self._solutions) >= 10 or self._number_of_attempts >= 50 or (self._number_of_attempts >= 10 and len(self._solutions) == 0)

    
    #override:
    #override the initialize function.  If there is no cantus firmus and line specified, generate one first
    def _initialize(self, cantus_firmus: list[RhythmicValue] = None, line: int = None) -> None:
        if cantus_firmus is None or line is None:
            cantus_firmus = self._cantus_firmus
            line = self._cantus_firmus_index
        super()._initialize(cantus_firmus=cantus_firmus, line=line)

    #override:
    #assign the highest and lowest notes based on the range of the Cantus Firmus
    def _assign_highest_and_lowest(self) -> None:

        #first get the highest and lowest notes of the Cantus Firmus
        c_highest, c_lowest = self._cantus_firmus[0], self._cantus_firmus[0]
        for note in self._cantus_firmus:
            if c_highest.get_chromatic_interval(note) > 0:
                c_highest = note 
            if c_lowest.get_chromatic_interval(note) < 0:
                c_lowest = note

        for line in range(self._height):
            if line != self._cantus_firmus_index:

                vocal_range = self._lines[line]
                #choose a range interval between an octave and tenth that is within each voice range
                range_size = randint(8, 10)
                leeway = 13 - range_size #this is the interval that we can add to the range_size interval to get the interval from the lowest to highest note available in the vocal range
                
                #if the Cantus Firmus is on top, we want to calculate our highest note in relation to the Cantus Firmus lowest note
                if line == 0:
                    high_vocal_highest = self._mode_resolver.get_highest_of_range(vocal_range)
                    low_vocal_highest = self._mode_resolver.get_default_pitch_from_interval(high_vocal_highest, leeway * -1)
                    high_possible_highest = high_vocal_highest if high_vocal_highest.get_tonal_interval(c_lowest) > -3 else self._mode_resolver.get_default_pitch_from_interval(c_lowest, 3)
                    low_possible_highest = low_vocal_highest if low_vocal_highest.get_tonal_interval(c_lowest) < 3 else self._mode_resolver.get_default_pitch_from_interval(c_lowest, -3)
                    tighter_leeway = low_possible_highest.get_tonal_interval(high_possible_highest)
                    if tighter_leeway < 0:
                        self._attempt_parameters[line]["highest"] = high_vocal_highest if low_vocal_highest.get_tonal_interval(c_lowest) > 0 else low_vocal_highest
                    else:
                        self._attempt_parameters[line]["highest"] = self._mode_resolver.get_default_pitch_from_interval(low_possible_highest, randint(1, tighter_leeway))
                    self._attempt_parameters[line]["lowest"] = self._mode_resolver.get_default_pitch_from_interval(self._attempt_parameters[line]["highest"], range_size * -1)
                else:
                    low_vocal_lowest = self._mode_resolver.get_lowest_of_range(vocal_range)
                    high_vocal_lowest = self._mode_resolver.get_default_pitch_from_interval(low_vocal_lowest, leeway)
                    low_possible_lowest = low_vocal_lowest if low_vocal_lowest.get_tonal_interval(c_highest) < 3 else self._mode_resolver.get_default_pitch_from_interval(c_highest, -3)
                    high_possible_lowest = high_vocal_lowest if high_vocal_lowest.get_tonal_interval(c_highest) > -3 else self._mode_resolver.get_default_pitch_from_interval(c_highest, 3)
                    tighter_leeway = low_possible_lowest.get_tonal_interval(high_possible_lowest)
                    if tighter_leeway < 0:
                        self._attempt_parameters[line]["lowest"] = low_vocal_lowest if high_vocal_lowest.get_tonal_interval(c_highest) < 0 else high_vocal_lowest
                    else:
                        self._attempt_parameters[line]["lowest"] = self._mode_resolver.get_default_pitch_from_interval(low_possible_lowest, randint(1, tighter_leeway))
                    self._attempt_parameters[line]["highest"] = self._mode_resolver.get_default_pitch_from_interval(self._attempt_parameters[line]["lowest"], range_size)


            else:
                self._attempt_parameters[line]["lowest"] = c_lowest
                self._attempt_parameters[line]["highest"] = c_highest
            
            self._attempt_parameters[line]["lowest_must_appear_by"] = randint(3, self._length - 1)
            self._attempt_parameters[line]["highest_must_appear_by"] = randint(3, self._length - 1)



    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500 or (self._number_of_solutions_found_this_attempt == 0 and self._number_of_backtracks > 1500):
            return True 
        return False 