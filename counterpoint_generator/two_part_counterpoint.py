import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from random import randint, random

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from mode_resolver import ModeResolver

from counterpoint_generator_subclasses import TwoPartCounterpoint
from counterpoint_generator_species_subclasses import FifthSpeciesCounterpointGenerator
from counterpoint_generator_solo_subclasses import CantusFirmusGenerator

from filter_functions.melodic_insertion_checks import begin_and_end_two_part_counterpoint
from filter_functions.melodic_insertion_checks import penultimate_bar_two_part_counterpoint


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
from filter_functions.harmonic_insertion_checks import resolves_predetermined_suspensions
from filter_functions.harmonic_insertion_checks import prevents_cross_relation_on_simultaneous_onsets
from filter_functions.harmonic_insertion_checks import handle_downbeats_two_part_counterpoint

from filter_functions.harmonic_rhythmic_filters import prepares_suspensions_fifth_species
from filter_functions.harmonic_rhythmic_filters import only_quarter_or_half_on_weak_half_note_dissonance
from filter_functions.harmonic_rhythmic_filters import prevents_simultaneous_syncopation
from filter_functions.harmonic_rhythmic_filters import handles_predetermined_suspensions
from filter_functions.harmonic_rhythmic_filters import handles_weak_half_note_dissonance_in_other_line
from filter_functions.harmonic_rhythmic_filters import handles_weak_quarter_note_dissonance_in_other_line


class TwoPartCounterpointGenerator (FifthSpeciesCounterpointGenerator, TwoPartCounterpoint):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        self._melodic_insertion_checks.append(begin_and_end_two_part_counterpoint)
        self._melodic_insertion_checks.append(penultimate_bar_two_part_counterpoint)

        self._harmonic_insertion_checks.append(adjacent_voices_stay_within_twelth)
        self._harmonic_insertion_checks.append(prevents_parallel_fifths_and_octaves_simple)
        self._harmonic_insertion_checks.append(forms_weak_quarter_beat_dissonance)
        self._harmonic_insertion_checks.append(resolves_weak_quarter_beat_dissonance_fifth_species)
        self._harmonic_insertion_checks.append(resolves_cambiata_tail)
        self._harmonic_insertion_checks.append(no_dissonant_onsets_on_downbeats)
        self._harmonic_insertion_checks.append(resolve_suspension)
        self._harmonic_insertion_checks.append(handles_weak_half_note_dissonance_fifth_species)
        self._harmonic_insertion_checks.append(resolves_weak_half_note_dissonance_fifth_species)
        self._harmonic_insertion_checks.append(resolves_predetermined_suspensions)
        self._harmonic_insertion_checks.append(prevents_cross_relation_on_simultaneous_onsets)
        self._harmonic_insertion_checks.append(handle_downbeats_two_part_counterpoint)

        self._harmonic_rhythmic_filters.append(prepares_suspensions_fifth_species)
        self._harmonic_rhythmic_filters.append(only_quarter_or_half_on_weak_half_note_dissonance)
        self._harmonic_rhythmic_filters.append(prevents_simultaneous_syncopation)
        self._harmonic_rhythmic_filters.append(handles_predetermined_suspensions)
        self._harmonic_rhythmic_filters.append(handles_weak_half_note_dissonance_in_other_line)
        self._harmonic_rhythmic_filters.append(handles_weak_quarter_note_dissonance_in_other_line)


    #override:
    #we should try ten attempts before we generate another Cantus Firmus
    def _exit_attempt_loop(self) -> bool:
        return len(self._solutions) >= 1 or (self._number_of_attempts >= 200 and len(self._solutions) == 0)

    
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
    #decide the number of Suspensions in advance
    def _initialize(self) -> None:
        super()._initialize()
        min_num_suspensions = randint(1, 2) if self._length < 12 else randint(2, 3)
        suspension_bars = [self._length - 2]
        for i in range(min_num_suspensions - 1):
            suspension_bar = randint(3, self._length - 2)
            while suspension_bar in suspension_bars:
                suspension_bar = randint(3, self._length - 2)
            suspension_bars.append(suspension_bar)
        for line in range(2):
            self._attempt_parameters[line]["suspension_bars"] = []
        for suspension_bar in suspension_bars:
            if random() < .33:
                self._attempt_parameters[0]["suspension_bars"].append(suspension_bar)
            else:
                self._attempt_parameters[1]["suspension_bars"].append(suspension_bar)

    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500 or (self._number_of_solutions_found_this_attempt == 0 and self._number_of_backtracks > 300):
            return True 
        return False 

    #override:
    #prevent Breves and Whole Notes from appearing in the middle of the line
    def _get_available_durations(self, line: int, bar: int, beat: float) -> set[int]:
        if bar == self._length - 1: return { 16 }
        if beat % 2 == 1.5: return { 1 }
        if beat % 2 == 1: return { 1, 2 }
        if beat == 2: return { 2, 4, 6, 8 }
        if beat == 0:
            if bar == 0: return { 2, 4, 6, 8, 12, 16 }
            else: return { 2, 4, 6, 8 }