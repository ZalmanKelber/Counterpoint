import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange

def form_suspension_fourth_species(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat == 2 and (bar + 1, 0) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar + 1, 0)]
        if c_note is not None:
            (t_interval, c_interval) = c_note.get_intervals(pitch)
            if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
                or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
                or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                if t_interval not in self._legal_intervals["resolvable_dissonance"]:
                    durations.discard(8)
    return durations