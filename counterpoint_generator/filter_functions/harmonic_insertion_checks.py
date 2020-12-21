import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange

#in First Species through Fourth Species, we only need to worry about parallels leading into downbeats
def prevents_parallel_fifths_and_octaves_simple(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
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
        interval = c_note.get_chromatic_interval(pitch)
        if interval > 0 and interval % 12 not in [0, 7]:
            return False 
        if interval < 0 and interval % 12 != 0:
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

#in the Second Species, we only need to worry about placing the Passing Tones themselves against the Cantus Firmus
def forms_passing_tone_second_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if beat == 2 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        c_note = self._counterpoint_objects[other_line][(bar, 0)]
        (t_interval, c_interval) = c_note.get_intervals(pitch)
        if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
            or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
            or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
            if abs(self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)) != 2:
                return False 
    return True 

def resolves_passing_tone_second_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if beat == 0 and len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        c_note = self._counterpoint_objects[other_line][(bar - 1, 0)]
        (t_interval, c_interval) = c_note.get_intervals(self._counterpoint_stacks[line][-1])
        if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
            or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
            or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
            if self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) != self._counterpoint_stacks[line][-1].get_tonal_interval(pitch):
                return False 
    return True 

#for use in Third and Fifth Species
def forms_weak_quarter_beat_dissonance(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2   
    if beat % 2 == 1 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        c_note = self._get_counterpoint_pitch(line, bar, beat)
        if c_note is not None:
            (t_interval, c_interval) = c_note.get_intervals(pitch)
            if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
                or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
                or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                if abs(self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)) != 2:
                    return False 
    return True  

#resolves Passing Tones, Lower Neighbors and Cambiatas
def resolves_weak_quarter_beat_dissonance_third_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if beat % 2 == 0 and len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        c_note = self._get_counterpoint_pitch(other_line, bar if beat > 0 else bar - 1, 1 if beat > 0 else 3)
        if c_note is not None:
            (t_interval, c_interval) = c_note.get_intervals(self._counterpoint_stacks[line][-1])
            if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
                or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
                or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                first_interval = self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1])
                second_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
                if (first_interval, second_interval) not in [(2, 2), (-2, -2), (-2, 2), (-2, -3)]:
                    return False 
    return True 

#resolves Passing Tones, Upper and Lower Neighbors and Cambiatas
def resolves_weak_quarter_beat_dissonance_fifth_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if beat % 2 == 0 and len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        c_note = self._get_counterpoint_pitch(other_line, bar if beat > 0 else bar - 1, 1 if beat > 0 else 3)
        if c_note is not None:
            (t_interval, c_interval) = c_note.get_intervals(self._counterpoint_stacks[line][-1])
            if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
                or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
                or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                first_interval = self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1])
                second_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
                if (first_interval, second_interval) not in [(2, 2), (-2, -2), (-2, 2), (2, -2), (-2, -3)]:
                    return False 
    return True 

#resolves fourth and potential fifth note of Cambiata, in both Third and Fifth Species
def resolves_cambiata_tail(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    camb_bar, cam_beat, res_bar, res_beat = None, None, None, None
    if beat in [1, 2]:
        (camb_bar, cam_beat) = (bar - 1, 3)
        (res_bar, res_beat) = (bar, 0)
    if beat == 0:
        (camb_bar, cam_beat) = (bar - 1, 1)
        (res_bar, res_beat) = (bar - 1, 2)
    else:
        (camb_bar, cam_beat) = (bar, 1)
        (res_bar, res_beat) = (bar, 2)
    if (camb_bar, cam_beat) in self._counterpoint_objects[line] and (res_bar, res_beat) in self._counterpoint_objects[line]:
        camb_note, res_note = self._counterpoint_objects[line][(camb_bar, cam_beat)], self._counterpoint_objects[line][(res_bar, res_beat)]
        if camb_note is None or res_note is None:
            print("camb_bar, camb_beat, res_bar, res_beat", camb_bar, cam_beat, res_bar, res_beat)
            self.print_counterpoint()
        if camb_note.get_tonal_interval(res_note) == -3:
            c_note = self._get_counterpoint_pitch(other_line, camb_bar, cam_beat)
            if c_note is not None:
                (t_interval, c_interval) = c_note.get_intervals(camb_note)
                if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
                    or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
                    or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                    if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != 2:
                        return False 
    return True

#for use only in Third Species
def strong_quarter_beats_are_consonant(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2   
    if beat % 2 == 0:
        c_note = self._get_counterpoint_pitch(other_line, bar, beat)
        if c_note is not None:
            (t_interval, c_interval) = c_note.get_intervals(pitch)
            if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
                or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
                or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                return False 
    return True




#used in all Two-part examples
#if both voices move in the same direction by a third or move, neither voice van move by a fifth or more
def prevents_large_leaps_in_same_direction(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch) and (bar, beat) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar, beat)]
        if c_note is not None:
            prev_beat = beat - 0.5 if beat > 0 else 3
            prev_bar = bar if beat > 0 else bar - 1
            prev_c_note = self._get_counterpoint_pitch(other_line, prev_bar, prev_beat)   
            interval, c_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch), prev_c_note.get_tonal_interval(c_note)
            if (interval > 2 and c_interval > 2) or (interval < 2 and c_interval < 2):
                if abs(interval) > 4 or abs(c_interval) > 4:
                    return False 
    return True   

#used in all Two-part examples
#a Note in one voice cannot immediately be followed by a Cross Relation of that Note in the other voice
def prevents_diagonal_cross_relations(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if (bar, beat) != (0, 0) and (bar, beat) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar, beat)]
        if c_note is not None:
            prev_beat = beat - 0.5 if beat > 0 else 3
            prev_bar = bar if beat > 0 else bar - 1
            prev_c_note = self._get_counterpoint_pitch(other_line, prev_bar, prev_beat)   
            prev_note = self._counterpoint_stacks[line][-1]
            if prev_c_note is not None and prev_c_note.is_cross_relation(pitch):
                return False 
            if isinstance(prev_note, Pitch) and prev_note.is_cross_relation(c_note):
                return False
    return True        

#used in all Two-part examples
#the top voice of an Open Fifth cannot be approached by ascending Half Step
def prevents_landini(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2     
    if (bar, beat) in self._counterpoint_objects[other_line] and (bar, beat) != (0, 0):
        c_note = self._counterpoint_objects[other_line][(bar, beat)]
        if c_note is not None and abs(c_note.get_chromatic_interval(pitch)) % 12 == 7:
            c_prev_note = self._get_counterpoint_pitch(other_line, bar if beat != 0 else bar - 1, beat - 0.5 if beat != 0 else 3)
            c_c_interval = c_prev_note.get_chromatic_interval(c_note)
            c_interval = self._counterpoint_stacks[line][-1].get_chromatic_interval(pitch)
            if { c_c_interval, c_interval } == { -2, 1 }:
                return False 
    return True 

#used in all Two-part examples
def resolve_suspension(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2  
    if beat in [1, 2] and (bar, 0) not in self._counterpoint_objects[line]:
        c_note, sus_note = self._get_counterpoint_pitch(other_line, bar, 0), self._get_counterpoint_pitch(line, bar, 0)
        if ( c_note.get_tonal_interval(sus_note) in self._legal_intervals["resolvable_dissonance"] and 
            sus_note.get_tonal_interval(pitch) != -2 ):
            return False 
    return True
