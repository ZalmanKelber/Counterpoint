import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange

#checks that Suspension Note is Consonant on onset and forms a Resolvable Dissonance on following Downbeat
def form_suspension_fourth_species(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat == 2 and (bar + 1, 0) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar, 0)]
        (t_interval, c_interval) = c_note.get_intervals(pitch)
        if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
            or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
            or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
            durations.discard(8)
        else:
            c_next_note = self._counterpoint_objects[other_line][(bar + 1, 0)]
            if c_next_note is not None:
                (t_interval, c_interval) = c_next_note.get_intervals(pitch)
                if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
                    or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
                    or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                    if t_interval not in self._legal_intervals["resolvable_dissonance"]:
                        durations.discard(8)
            
    return durations

#also makes sure that the second Downbeat of a Breve is a Consonant
def prepares_suspensions_fifth_species(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat % 2 == 0 and bar < self._length - 1:
        c_note = self._get_counterpoint_pitch(other_line, bar + 1, 0)
        if c_note is not None:
            (t_interval, c_interval) = c_note.get_intervals(pitch)
            if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
                or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
                or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                durations.discard(16)
                if t_interval not in self._legal_intervals["resolvable_dissonance"]:
                    if beat == 0:
                        durations.discard(12)
                    if beat == 2:
                        durations.discard(8)
                        durations.discard(6)
    return durations

#we must end on a cadence
def handle_antipenultimate_bar_of_fifth_species_against_cantus_firmus(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if bar == self._length - 3:
        if beat == 0:
            durations.discard(16)
            durations.discard(12)
            durations.discard(8)
            durations.discard(6)
        if beat == 2:
            durations.discard(4)
            durations.discard(2)
            c_note = self._counterpoint_objects[other_line][(self._length - 2, 0)]
            if c_note is not None and c_note.get_tonal_interval(pitch) not in self._legal_intervals["resolvable_dissonance"]:
                return set()
    return durations

#used in Fifth Species
def only_quarter_or_half_on_weak_half_note_dissonance(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat == 2:
        c_note = self._get_counterpoint_pitch(other_line, bar, beat)
        if c_note is not None:
            (t_interval, c_interval) = c_note.get_intervals(pitch)
            if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
                or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
                or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                durations.discard(8)
                durations.discard(6)
                if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != -2:
                    durations.discard(2)
    return durations

#used in Two-part polyphony 
def prevents_simultaneous_syncopation(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat == 0 and bar < self._length - 1 and (bar + 1, 0) not in self._counterpoint_objects[other_line]:
        durations.discard(12)
    elif beat == 2 and bar < self._length - 1 and (bar + 1, 0) not in self._counterpoint_objects[other_line]:
        durations.discard(8)
        durations.discard(6)
    return durations

#ensure that the correct voices are forming Suspensions where specified in the Attempt Parameters
def handles_predetermined_suspensions(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat == 0 and bar + 1 in self._attempt_parameters[line]["suspension_bars"]:
        durations.discard(8)
        durations.discard(6)
    if beat == 2 and bar + 1 in self._attempt_parameters[line]["suspension_bars"]:
        c_note = self._get_counterpoint_pitch(other_line, bar + 1, 0)
        if c_note is not None and c_note.get_tonal_interval(pitch) not in self._legal_intervals["resolvable_dissonance"]:
            return set()
        durations.discard(4)
        durations.discard(2)
    if beat == 2 and bar + 1 in self._attempt_parameters[other_line]["suspension_bars"]:
        durations.discard(8)
        durations.discard(6)
    return durations

