import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from abc import ABC

from counterpoint_generator import CounterpointGenerator
from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from mode_resolver import ModeResolver

from filter_functions.melodic_insertion_checks import begin_and_end_on_mode_final
from filter_functions.rhythmic_insertion_filters import end_on_breve

class SoloMelody (CounterpointGenerator, ABC):

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
        super().__init__(self, length, lines, mode)
        self._legal_intervals["tonal_harmonic_consonant"] = { 1, 3, 5, 6 } #note that these are all mod 7 and absolute values 
        self._legal_intervals["tonal_chromatic_consonant"] = { 0, 3, 4, 7, 8, 9 } #mod 12, absolute value
        #tonal intervals that can be resolved via suspension:
        self._legal_intervals["resolvable_dissonance"] = { -9, -2, 4, 7, 11, 14, 18, 21 } 
        self._harmonic_insertion_checks = []
        self._harmonic_rhythmic_filters = []

    ##################### override methods #######################

    #to pass the insertion checks, pitches must pass the melodic and harmonic insertion checks
    def _passes_insertion_checks(self, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
        for check in self._melodic_insertion_checks:
            if not check(pitch, line, bar, beat): return False 
        for check in self._harmonic_insertion_checks:
            if not check(pitch, line, bar, beat): return False
        return True 

    #likewise, durations must be filtered through harmonic checks as well
    def _get_valid_durations(self, pitch: Pitch, line: int, bar: int, beat: float) -> set[int]:
        durations = get_available_durations(line, bar, beat)
        for check in self._rhythmic_insertion_filters:
            durations = check(pitch, line, bar, beat, durations)
            if len(durations) == 0: return durations
        for check in self._harmonic_rhythmic_filters:
            durations = check(pitch, line, bar, beat, durations)
            if len(durations) == 0: return durations
        return durations

    #retrieves the note currently beginning on or sustaining through the specified index on the specified line
    def _get_counterpoint_pitch(self, line: int, bar: int, beat: int) -> Pitch:
        while (bar, beat) not in self._counterpoint_objects[line]: 
            beat -= 0.5
            if beat < 0:
                beat += 4
                bar -= 1
        return self._counterpoint_objects[line][(bar, beat)] if isinstance(self._counterpoint_objects[line][(bar, beat)], Pitch) else None 

        


class TwoPartCounterpoint (MultiPartCounterpoint, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        if len(lines) != 2:
            raise Exception("Two-part Counterpoint must have two lines")
        super().__init__(self, length, lines, mode)

        self._rhythmic_insertion_filters.append(end_on_breve)

        
    

    
    
