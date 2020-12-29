from random import randint, random

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

from two_lines import TwoLines
from fifth_species import FifthSpeciesCounterpointGenerator
from cantus_firmus import CantusFirmusGenerator

from filter_functions.melodic_insertion_checks import end_stepwise

from filter_functions.harmonic_insertion_checks import unison_not_allowed_on_downbeat_outside_first_and_last_measure
from filter_functions.harmonic_insertion_checks import adjacent_voices_stay_within_twelth
from filter_functions.harmonic_insertion_checks import forms_passing_tone_second_species
from filter_functions.harmonic_insertion_checks import resolves_passing_tone_second_species
from filter_functions.harmonic_insertion_checks import prevents_parallel_fifths_and_octaves_simple
from filter_functions.harmonic_insertion_checks import forms_weak_quarter_beat_dissonance
from filter_functions.harmonic_insertion_checks import resolves_weak_quarter_beat_dissonance_fifth_species
from filter_functions.harmonic_insertion_checks import resolves_cambiata_tail
from filter_functions.harmonic_insertion_checks import no_dissonant_onsets_on_downbeats
from filter_functions.harmonic_insertion_checks import resolve_suspension
from filter_functions.harmonic_insertion_checks import handles_weak_half_note_dissonance_fifth_species
from filter_functions.harmonic_insertion_checks import resolves_weak_half_note_dissonance_fifth_species

from filter_functions.harmonic_rhythmic_filters import prepares_suspensions_fifth_species
from filter_functions.harmonic_rhythmic_filters import handle_antipenultimate_bar_of_fifth_species_against_cantus_firmus
from filter_functions.harmonic_rhythmic_filters import only_quarter_or_half_on_weak_half_note_dissonance

from filter_functions.score_functions import find_as_many_suspensions_as_possible


class TwoPartFifthSpeciesGenerator (FifthSpeciesCounterpointGenerator, TwoLines):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode, cantus_firmus_index: int = 0):
        super().__init__(length, lines, mode)
        if cantus_firmus_index not in [0, 1]:
            raise Exception("invalid cantus firmus index")

        self._melodic_insertion_checks.append(end_stepwise)

        # self._harmonic_insertion_checks.append(unison_not_allowed_on_downbeat_outside_first_and_last_measure)
        self._harmonic_insertion_checks.append(adjacent_voices_stay_within_twelth)
        self._harmonic_insertion_checks.append(prevents_parallel_fifths_and_octaves_simple)
        self._harmonic_insertion_checks.append(forms_weak_quarter_beat_dissonance)
        self._harmonic_insertion_checks.append(resolves_weak_quarter_beat_dissonance_fifth_species)
        self._harmonic_insertion_checks.append(resolves_cambiata_tail)
        self._harmonic_insertion_checks.append(no_dissonant_onsets_on_downbeats)
        self._harmonic_insertion_checks.append(resolve_suspension)
        self._harmonic_insertion_checks.append(handles_weak_half_note_dissonance_fifth_species)
        self._harmonic_insertion_checks.append(resolves_weak_half_note_dissonance_fifth_species)
        
        self._harmonic_rhythmic_filters.append(prepares_suspensions_fifth_species)
        self._harmonic_rhythmic_filters.append(handle_antipenultimate_bar_of_fifth_species_against_cantus_firmus)
        self._harmonic_rhythmic_filters.append(only_quarter_or_half_on_weak_half_note_dissonance)

        self._score_functions.append(find_as_many_suspensions_as_possible)

        #create the cantus firmus we'll use
        self._cantus_firmus_index = cantus_firmus_index
        self._cantus_firmus = None
        last_leap = 5 if mode == Mode.PHRYGIAN else 4
        #in the Fifth Species, it will be necessary to find a Cantus Firmus that ends in a way that allows us to cadence
        while self._cantus_firmus is None or self._cantus_firmus[-2].get_tonal_interval(self._cantus_firmus[-1]) not in [-2, last_leap]:
            cantus_firmus_generator = CantusFirmusGenerator(self._length, [self._lines[self._cantus_firmus_index]], self._mode)
            cantus_firmus_generator.generate_counterpoint(must_end_by_descending_step=True if self._cantus_firmus_index == 1 else False)
            cantus_firmus_generator.score_solutions()
            solution = cantus_firmus_generator.get_one_solution()
            self._cantus_firmus = solution[0] if solution is not None else None

    #override:
    #we should try ten attempts before we generate another Cantus Firmus
    def _exit_attempt_loop(self) -> bool:
        return len(self._solutions) >= 40 or self._number_of_attempts >= 50 or (self._number_of_attempts >= 40 and len(self._solutions) == 0)

    
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
        if self._number_of_backtracks > 3500 or (self._number_of_solutions_found_this_attempt == 0 and self._number_of_backtracks > 1000):
            return True 
        return False 