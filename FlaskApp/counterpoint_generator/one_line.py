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

from filter_functions.melodic_insertion_checks import begin_and_end_on_mode_final

from filter_functions.rhythmic_insertion_filters import end_on_breve
from filter_functions.rhythmic_insertion_filters import pentultimate_note_is_leading_tone

from filter_functions.harmonic_insertion_checks import sharp_notes_and_leading_tones_not_doubled

from filter_functions.harmonic_insertion_checks import prevents_hidden_fifths_and_octaves_two_part
from filter_functions.harmonic_insertion_checks import no_dissonant_onsets_on_downbeats
from filter_functions.harmonic_insertion_checks import start_and_end_intervals_two_part
from filter_functions.harmonic_insertion_checks import prevents_large_leaps_in_same_direction
from filter_functions.harmonic_insertion_checks import prevents_diagonal_cross_relations
from filter_functions.harmonic_insertion_checks import prevents_landini

from filter_functions.score_functions import penalize_perfect_intervals_on_downbeats

class OneLine (CounterpointGenerator, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        if len(lines) != 1:
            raise Exception("Solo Melody must only have one line")
        super().__init__(length, lines, mode)
        self._melodic_insertion_checks.append(begin_and_end_on_mode_final)

        self._rhythmic_insertion_filters.append(end_on_breve)

    #override:
    #in an unaccompanied melody, no rests are allowed 
    def _get_valid_rest_durations(self, line: int, bar: int, beat: float) -> set[int]:
        return set()


class MultiPartCounterpoint (CounterpointGenerator, ABC):

    #with more than one line, pitches must be run through harmonic insertion checks
    #in addition to melodic insertion checks
    _harmonic_insertion_checks = [] 

    #similarly, rhythmic filters must take into consideration the harmonic context
    _harmonic_rhythmic_filters = []

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        if len(lines) < 2:
            raise Exception("Multi-part Counterpoint must have at least two lines")

        if not self._lines_are_valid(lines):
            raise Exception("Invalid vocal ranges entered.  Either ranges were not in order or Soprano and Bass were adjacent")
        super().__init__(length, lines, mode)

        self._legal_intervals["tonal_harmonic_consonant"] = { 1, 3, 5, 6 } #note that these are all mod 7 and absolute values 
        self._legal_intervals["chromatic_harmonic_consonant"] = { 0, 3, 4, 7, 8, 9 } #mod 12, absolute value
        #tonal intervals that can be resolved via suspension:
        self._legal_intervals["resolvable_dissonance"] = { -9, -2, 4, 7, 11, 14, 18, 21 } 
        self._harmonic_insertion_checks = []
        self._harmonic_rhythmic_filters = []

        self._rhythmic_insertion_filters.append(pentultimate_note_is_leading_tone)

        self._harmonic_insertion_checks.append(sharp_notes_and_leading_tones_not_doubled)

    
    #override:
    #to pass the insertion checks, pitches must pass the melodic and harmonic insertion checks
    def _passes_insertion_checks(self, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
        for check in self._melodic_insertion_checks:
            if not check(self, pitch, line, bar, beat): 
                if self._highest_index_reached == (line, bar, beat):
                    self._log.append(str(pitch) + " " + str((line, bar, beat)))
                    self._log.append(check.__name__)
                    # print(pitch)
                    # print("failed at check", check.__name__)
                return False 
        for check in self._harmonic_insertion_checks:
            if not check(self, pitch, line, bar, beat): 
                if self._highest_index_reached == (line, bar, beat):
                    self._log.append(str(pitch) + " " + str((line, bar, beat)))
                    self._log.append(check.__name__)
                    # print(pitch)
                    # print("failed at check", check.__name__)
                return False
        return True 

    #override:
    #likewise, durations must be filtered through harmonic checks as well
    def _get_valid_durations(self, pitch: Pitch, line: int, bar: int, beat: float) -> set[int]:
        durations = self._get_available_durations(line, bar, beat)
        for check in self._rhythmic_insertion_filters:
            prev_len = len(durations)
            durations = check(self, pitch, line, bar, beat, durations)
            # if len(durations) != prev_len:
            #     print(pitch)
            #     print("failed at check", check.__name__)
            if len(durations) == 0: 
                if self._highest_index_reached == (line, bar, beat):
                    self._log.append(str(pitch) + " " + str((line, bar, beat)))
                    self._log.append(check.__name__)
                return durations
        for check in self._harmonic_rhythmic_filters:
            prev_len = len(durations)
            durations = check(self, pitch, line, bar, beat, durations)
            # if len(durations) != prev_len:
            #     print(pitch)
            #     print("failed at check", check.__name__)
            if len(durations) == 0: 
                if self._highest_index_reached == (line, bar, beat):
                    self._log.append(str(pitch) + " " + str((line, bar, beat)))
                    self._log.append(check.__name__)
                return durations
        return durations

    #retrieves the note currently beginning on or sustaining through the specified index on the specified line
    def _get_counterpoint_pitch(self, line: int, bar: int, beat: int) -> Pitch:
        while (bar, beat) not in self._counterpoint_objects[line]: 
            beat -= 0.5
            if beat < 0:
                beat += 4
                bar -= 1
        return self._counterpoint_objects[line][(bar, beat)] if isinstance(self._counterpoint_objects[line][(bar, beat)], Pitch) else None 

    #public function: adds melody or Cantus Firmus to the counterpoint structure
    def assign_melody_to_line(self, melody: list[RhythmicValue], line: int) -> None:
        bar, beat = 0, 0
        for entity in melody:
            self._remaining_indices[line].pop()
            self._counterpoint_stacks[line].append(entity)
            self._counterpoint_objects[line][(bar, beat)] = entity
            for half_beat in range(entity.get_duration()):
                beat += .5
                if beat >= 4:
                    beat -= 4
                    bar += 1
                #note that this step isn't done on the last iteration
                if (bar, beat) in self._counterpoint_objects[line] and half_beat != entity.get_duration() - 1:
                    del self._counterpoint_objects[line][(bar, beat)]
                    self._all_indices[line].remove((bar, beat))
                    self._remaining_indices[line].pop()

    #follows same procedure but adds existing Cantus Firmus to lines
    def gnerate_counterpoint_from_cantus_firmus(self, cantus_firmus: list[RhythmicValue], line: int) -> None:
        self._number_of_attempts = 0
        while not self._exit_attempt_loop():
            self._number_of_attempts += 1
            self._initialize(cantus_firmus, line)
            self._backtrack()
            print("number of solutions:", len(self._solutions), "number of backtracks:", self._number_of_backtracks)
        return 
            
    #override:
    #if a Cantus Firmus or line is given, assign it to the Counterpoint stack and object
    def _initialize(self, cantus_firmus: list[RhythmicValue] = None, line: int = None) -> None:
        super()._initialize()
        if cantus_firmus is not None and line is not None:
            self.assign_melody_to_line(cantus_firmus, line)

    #Vocal Ranges must be given in ascending order, and Soprano and Bass may not be adjacent
    def _lines_are_valid(self, lines: list[VocalRange]) -> bool:
        for i in range(len(lines) - 1):
            lower, higher = lines[i], lines[i + 1]
            if (lower, higher) == (VocalRange.BASS, VocalRange.SOPRANO):
                return False 
            if lower.value > higher.value:
                return False 
        return True

    #helper function used in many of the filter functions
    def _is_consonant(self, pitch1: Pitch, pitch2: Pitch) -> bool:
        (t_interval, c_interval) = pitch1.get_intervals(pitch2)
        if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
            or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
            or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
            return False 
        if ( (self._mode_resolver.is_sharp(pitch1) or self._mode_resolver.is_leading_tone(pitch1)) 
            and (self._mode_resolver.is_sharp(pitch2) or self._mode_resolver.is_leading_tone(pitch2)) ):
            return False
        return True
            


class TwoPartCounterpoint (MultiPartCounterpoint, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        if len(lines) != 2:
            raise Exception("Two-part Counterpoint must have two lines")
        super().__init__(length, lines, mode)

        self._rhythmic_insertion_filters.append(end_on_breve)

        self._harmonic_insertion_checks.append(prevents_hidden_fifths_and_octaves_two_part)
        self._harmonic_insertion_checks.append(no_dissonant_onsets_on_downbeats)
        self._harmonic_insertion_checks.append(start_and_end_intervals_two_part)
        self._harmonic_insertion_checks.append(prevents_large_leaps_in_same_direction)
        self._harmonic_insertion_checks.append(prevents_diagonal_cross_relations)
        self._harmonic_insertion_checks.append(prevents_landini)

        self._score_functions.append(penalize_perfect_intervals_on_downbeats)

        
    

    
    
