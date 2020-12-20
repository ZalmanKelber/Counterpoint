import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange

#in First Species, we only need to worry about parallels on successive downbeats
def prevents_parallel_fifths_and_octaves_first_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if bar != 0:
        prev_note = self._counterpoint_stacks[line][-1]
        for other_line in range(self._height):
            if other_line != line:
                prev_c_note, c_note = self._counterpoint_objects[other_line][(bar - 1, 0)], self._counterpoint_objects[other_line][(bar, 0)]
                if prev_c_note is not None and c_note is not None:
                    first_interval = prev_c_note.get_chromatic_interval(prev_note)
                    if abs(first_interval) % 12 in [0, 7] and first_interval == c_note.get_chromatic_interval(pitch):
                        return False 
    return True
            

#blocks parallel motion leading to perfect intervals
def prevents_hidden_fifths_and_octaves_two_part(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2
    if (bar, beat) != (0, 0) and (bar, beat) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar, beat)]
        if c_note is not None and abs(c_note.get_chromatic_interval(pitch)) % 12 in [0,7]:
            prev_beat = beat - 0.5 if beat > 0 else 3.5
            prev_bar = bar if beat > 0 else bar - 1
            prev_note = self._get_counterpoint_pitch(line, prev_bar, prev_beat)
            prev_c_note = self._get_counterpoint_pitch(other_line, prev_bar, prev_beat)
            interval, c_interval = prev_note.get_tonal_interval(pitch), prev_c_note.get_tonal_interval(c_note)
            if (interval > 0 and c_interval > 0) or (interval < 0 and c_interval < 0):
                return False 
    return True

#used in First Species through Fourth Species
def unison_not_allowed_on_downbeat_outside_first_and_last_measure(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2
    if beat == 0 and bar not in [0, self._length - 1]:
        if (bar, beat) in self._counterpoint_objects[other_line]:
            c_note = self._counterpoint_objects[other_line][(bar, beat)]
            if c_note is not None and c_note.is_unison(pitch):
                return False 
    return True 

#used in all Two Part examples
def no_dissonant_onsets_on_downbeats(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2
    if beat == 0 and (bar, beat) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar, beat)]
        if c_note is not None:
            (t_interval, c_interval) = c_note.get_intervals(pitch)
            if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] or 
                abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] or 
                (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                return False 
    return True

#in Two Parts we must start and end on Unisons, Fifths or Octaves
def start_and_end_intervals_two_part(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2
    c_note = None 
    if len(self._counterpoint_stacks[line]) == 0 or not isinstance(self._counterpoint_stacks[line][-1], Pitch):
        c_note = self._get_counterpoint_pitch(other_line, bar, beat)
    if bar == self._length - 1:
        c_note = self._counterpoint_objects[other_line][(self._length - 1, 0)]
    if c_note is not None:
        if abs(c_note.get_chromatic_interval(pitch)) not in [0, 7, 12]:
            return False 
    return True
    
#for use in First Species
def no_more_than_four_consecutive_repeated_vertical_intervals(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if bar >= 3:
        note_1 = self._counterpoint_objects[line][(bar - 3, 0)]
        note_2 = self._counterpoint_objects[line][(bar - 2, 0)]
        note_3 = self._counterpoint_objects[line][(bar - 1, 0)]
        for other_line in range(self._height):
            if other_line != line:
                c_note_1 = self._counterpoint_objects[other_line][(bar - 3, 0)]
                c_note_2 = self._counterpoint_objects[other_line][(bar - 2, 0)]
                c_note_3 = self._counterpoint_objects[other_line][(bar - 1, 0)]
                c_note_4 = self._counterpoint_objects[other_line][(bar, 0)]
                if c_note_4 is not None:
                    interval_1 = abs(c_note_1.get_tonal_interval(note_1))
                    interval_2 = abs(c_note_2.get_tonal_interval(note_2))
                    interval_3 = abs(c_note_3.get_tonal_interval(note_3))
                    interval_4 = abs(c_note_4.get_tonal_interval(pitch))
                    if interval_4 == interval_3 and interval_3 == interval_2 and interval_2 == interval_1:
                        return False
    return True

#prevents adjacent voices from mobing further than a tenth from each other
def adjacent_voices_stay_within_tenth(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    for other_line in [line - 1, line + 1]:
        if other_line >= 0 and other_line < self._height:
            c_note = self._get_counterpoint_pitch(other_line, bar, beat)
            if c_note is not None and abs(c_note.get_tonal_interval(pitch)) > 10:
                return False 
    return True

#prevents adjacent voices from mobing further than a twelth from each other
def adjacent_voices_stay_within_twelth(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    for other_line in [line - 1, line + 1]:
        if other_line >= 0 and other_line < self._height:
            c_note = self._get_counterpoint_pitch(other_line, bar, beat)
            if c_note is not None and abs(c_note.get_tonal_interval(pitch)) > 12:
                return False 
    return True

#used in all multi-part examples
def sharp_notes_and_leading_tones_not_doubled(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if self._mode_resolver.is_sharp(pitch) or self._mode_resolver.is_leading_tone(pitch):
        for other_line in range(self._height):
            if other_line != line:
                c_note = self._get_counterpoint_pitch(other_line, bar, beat)
                if c_note is not None and abs(c_note.get_chromatic_interval(pitch)) % 12 == 0:
                    return False 
    return True
                

