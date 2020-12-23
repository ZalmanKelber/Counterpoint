import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from random import randint, random

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from mode_resolver import ModeResolver

from counterpoint_generator_subclasses import TwoPartCounterpoint
from counterpoint_generator_species_subclasses import FifthSpeciesCounterpointGenerator
from counterpoint_generator_solo_subclasses import CantusFirmusGenerator


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


class TwoPartCounterpointGenerator (FifthSpeciesCounterpointGenerator, TwoPartCounterpoint):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

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


    #override:
    #we should try ten attempts before we generate another Cantus Firmus
    def _exit_attempt_loop(self) -> bool:
        return len(self._solutions) >= 40 or self._number_of_attempts >= 50 or (self._number_of_attempts >= 40 and len(self._solutions) == 0)

    
    # #override:
    # #override the initialize function.  If there is no cantus firmus and line specified, generate one first
    # def _initialize(self, cantus_firmus: list[RhythmicValue] = None, line: int = None) -> None:
    
    #     super()._initialize(cantus_firmus=cantus_firmus, line=line)

    #override:
    #assign the highest and lowest notes based on the range of the Cantus Firmus
    def _assign_highest_and_lowest(self) -> None:

        #determine range for bottom line:
        range_size = randint(8, 10)
        leeway = 13 - range_size
        vocal_lowest = self._mode_resolver.get_lowest_of_range(self._lines[0])
        self._attempt_parameters[0]["lowest"] = self._mode_resolver.get_default_pitch_from_interval(vocal_lowest, randint(1, leeway))
        self._attempt_parameters[0]["highest"] = self._mode_resolver.get_default_pitch_from_interval(self._attempt_parameters[0]["lowest"], range_size)
        
       
        #use this to determine range for top line
        c_highest = self._attempt_parameters[0]["highest"]
        range_size = randint(8, 10)
        leeway = 13 - range_size #this is the interval that we can add to the range_size interval to get the interval from the lowest to highest note available in the vocal range
        low_vocal_lowest = self._mode_resolver.get_lowest_of_range(self._lines[1])
        high_vocal_lowest = self._mode_resolver.get_default_pitch_from_interval(low_vocal_lowest, leeway)
        low_possible_lowest = low_vocal_lowest if low_vocal_lowest.get_tonal_interval(c_highest) < 3 else self._mode_resolver.get_default_pitch_from_interval(c_highest, -3)
        high_possible_lowest = high_vocal_lowest if high_vocal_lowest.get_tonal_interval(c_highest) > -3 else self._mode_resolver.get_default_pitch_from_interval(c_highest, 3)
        tighter_leeway = low_possible_lowest.get_tonal_interval(high_possible_lowest)
        if tighter_leeway < 0:
            self._attempt_parameters[1]["lowest"] = low_vocal_lowest if high_vocal_lowest.get_tonal_interval(c_highest) < 0 else high_vocal_lowest
        else:
            self._attempt_parameters[1]["lowest"] = self._mode_resolver.get_default_pitch_from_interval(low_possible_lowest, randint(1, tighter_leeway))
        self._attempt_parameters[1]["highest"] = self._mode_resolver.get_default_pitch_from_interval(self._attempt_parameters[1]["lowest"], range_size)


        for line in range(2):
            self._attempt_parameters[line]["lowest_must_appear_by"] = randint(3, self._length - 1)
            self._attempt_parameters[line]["highest_must_appear_by"] = randint(3, self._length - 1)



    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500 or (self._number_of_solutions_found_this_attempt == 0 and self._number_of_backtracks > 1000):
            return True 
        return False 