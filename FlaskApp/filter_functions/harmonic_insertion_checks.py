import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

#in First Species through Fourth Species, we only need to worry about parallels leading into downbeats
def prevents_parallel_fifths_and_octaves_simple(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if bar != 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        prev_note = self._counterpoint_stacks[line][-1]
        for other_line in range(self._height):
            if other_line != line and (bar - 1, 0) in self._counterpoint_objects[other_line] and (bar, 0) in self._counterpoint_objects[other_line]:
                prev_c_note, c_note = self._counterpoint_objects[other_line][(bar - 1, 0)], self._counterpoint_objects[other_line][(bar, 0)]
                if prev_c_note is not None and c_note is not None and isinstance(prev_c_note, Pitch):
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
            if prev_note is not None and prev_c_note is not None:
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
        c_note = self._counterpoint_objects[other_line][(bar, beat)] if (bar, beat) in self._counterpoint_objects[other_line] else None
        if c_note is not None and isinstance(c_note, Pitch):
            if not self._is_consonant(c_note, pitch):
                return False 
    return True

#in Two Parts we must start and end on Unisons, Fifths or Octaves
def start_and_end_intervals_two_part(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2
    c_note = None 
    if len(self._counterpoint_stacks[line]) == 0 or not isinstance(self._counterpoint_stacks[line][-1], Pitch):
        c_note = self._get_counterpoint_pitch(other_line, bar, beat)
    if bar == self._length - 1:
        if (self._length - 1, 0) not in self._counterpoint_objects[other_line]:
            print(self._counterpoint_objects[other_line])
            self.print_counterpoint()
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
        if not self._is_consonant(c_note, pitch):
            if abs(self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)) != 2:
                return False 
    return True 

def resolves_passing_tone_second_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if beat == 0 and len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        c_note = self._counterpoint_objects[other_line][(bar - 1, 0)]
        if not self._is_consonant(c_note, self._counterpoint_stacks[line][-1]):
            if self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) != self._counterpoint_stacks[line][-1].get_tonal_interval(pitch):
                return False 
    return True 

#for use in Third and Fifth Species
def forms_weak_quarter_beat_dissonance(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2  
    if beat % 2 == 1 and len(self._counterpoint_stacks[line]) == 0:
        print(line, bar, beat)
        self.print_counterpoint() 
    if beat % 2 == 1 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        c_note = self._get_counterpoint_pitch(line, bar, beat)
        if c_note is not None:
            if not self._is_consonant(c_note, pitch):
                    return False 
    return True  

#resolves Passing Tones, Lower Neighbors and Cambiatas
def resolves_weak_quarter_beat_dissonance_third_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if beat % 2 == 0 and len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        c_note = self._get_counterpoint_pitch(other_line, bar if beat > 0 else bar - 1, 1 if beat > 0 else 3)
        if c_note is not None:
            if not self._is_consonant(c_note, self._counterpoint_stacks[line][-1]):
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
            if not self._is_consonant(c_note, self._counterpoint_stacks[line][-1]):
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
    if beat == 3:
        (camb_bar, cam_beat) = (bar, 1)
        (res_bar, res_beat) = (bar, 2)
    if (camb_bar, cam_beat) in self._counterpoint_objects[line] and (res_bar, res_beat) in self._counterpoint_objects[line]:
        camb_note, res_note = self._counterpoint_objects[line][(camb_bar, cam_beat)], self._counterpoint_objects[line][(res_bar, res_beat)]
        if camb_note.get_tonal_interval(res_note) == -3:
            c_note = self._get_counterpoint_pitch(other_line, camb_bar, cam_beat)
            if c_note is not None:
                if not self._is_consonant(c_note, camb_note):
                    if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != 2:
                        return False 
    return True

#for use only in Third Species
def strong_quarter_beats_are_consonant(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2   
    if beat % 2 == 0:
        c_note = self._get_counterpoint_pitch(other_line, bar, beat)
        if c_note is not None:
            if not self._is_consonant(c_note, pitch):
                return False 
    return True




#used in all Two-part examples
#if both voices move in the same direction by a third or move, neither voice van move by a fifth or more
def prevents_large_leaps_in_same_direction(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch) and (bar, beat) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar, beat)]
        if c_note is not None and isinstance(c_note, Pitch):
            prev_beat = beat - 0.5 if beat > 0 else 3
            prev_bar = bar if beat > 0 else bar - 1
            prev_c_note = self._get_counterpoint_pitch(other_line, prev_bar, prev_beat)   
            if isinstance(prev_c_note, Pitch):
                interval, c_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch), prev_c_note.get_tonal_interval(c_note)
                if (interval > 2 and c_interval > 2) or (interval < 2 and c_interval < 2):
                    if abs(interval) > 4 or abs(c_interval) > 4:
                        return False 
    return True   

#used in all Two-part examples
#a Note in one voice cannot immediately be followed by a Cross Relation of that Note in the other voice
def prevents_diagonal_cross_relations(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2    
    if (bar, beat) != (0, 0) and (bar, beat) in self._counterpoint_objects[other_line] and len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
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
        if isinstance(c_note, Pitch) and abs(c_note.get_chromatic_interval(pitch)) % 12 == 7:
            if c_note.get_tonal_interval(pitch) < 0:
                c_prev_note = self._get_counterpoint_pitch(other_line, bar if beat != 0 else bar - 1, beat - 0.5 if beat != 0 else 3)
                if isinstance(c_prev_note, Pitch) and c_prev_note.get_chromatic_interval(c_note) == 1:
                    return False 
            else:
                if isinstance(self._counterpoint_stacks[line][-1], Pitch) and self._counterpoint_stacks[line][-1].get_chromatic_interval(pitch) == 1:
                    return False 
    return True 

#used in all Two-part examples
def resolve_suspension(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2  
    if beat in [1, 2] and (bar, 0) not in self._counterpoint_objects[line]:
        c_note, sus_note = self._get_counterpoint_pitch(other_line, bar, 0), self._get_counterpoint_pitch(line, bar, 0)
        if ( c_note is not None and c_note.get_tonal_interval(sus_note) in self._legal_intervals["resolvable_dissonance"] and 
            sus_note.get_tonal_interval(pitch) != -2 ):
            return False 
    return True

#handles Passing Tones on middle beat of Measure
def handles_weak_half_note_dissonance_fifth_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2 
    if beat == 2:
        c_note = self._get_counterpoint_pitch(other_line, bar, beat)
        if c_note is not None:
            if not self._is_consonant(c_note, pitch):
                prev = self._counterpoint_stacks[line][-1]
                if isinstance(prev, Pitch) and abs(prev.get_tonal_interval(pitch)) != 2:
                    return False 
                if (bar, beat) in self._counterpoint_objects[other_line]:
                    return False
    return True

#must resolve by step in same direction as previous interval
def resolves_weak_half_note_dissonance_fifth_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2 
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if (beat == 3 and self._counterpoint_stacks[line][-1].get_duration() == 2) or (beat == 0 and self._counterpoint_stacks[line][-1].get_duration() == 4):
            (prev_bar, prev_beat) = (bar - 1, 2) if beat == 0 else (bar, 2)
            c_note = self._get_counterpoint_pitch(other_line, prev_bar, prev_beat)
            if c_note is not None:
                if not self._is_consonant(c_note, self._counterpoint_stacks[line][-1]):
                    if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]):
                        return False 
    return True

#ensures that all predetermined Suspensions are resolvable Dissonances
def resolves_predetermined_suspensions(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2 
    if (beat == 1 or beat == 2) and bar in self._attempt_parameters[line]["suspension_bars"]:
        if self._counterpoint_objects[line][(bar - 1, 2)].get_tonal_interval(pitch) != -2:
            return False 
    if beat == 0 and bar in self._attempt_parameters[other_line]["suspension_bars"]:
        c_note = self._counterpoint_objects[other_line][(bar - 1, 2)]
        if c_note is not None and c_note.get_tonal_interval(pitch) not in self._legal_intervals["resolvable_dissonance"]:
            return False
    if beat == 2 and bar + 1 in self._attempt_parameters[line]["suspension_bars"] and bar == self._length - 3:
        return self._mode_resolver.is_final(pitch)
    if beat == 0 and bar + 1 in self._attempt_parameters[line]["suspension_bars"] and bar == self._length - 3:
        return not self._mode_resolver.is_final(pitch)
    #we also want to ensure that Notes against which a Suspension in another voice will resolve to will form valid intervals
    if beat == 2 and line == 0 and bar in self._attempt_parameters[other_line]["suspension_bars"]:
        mel_interval = self._counterpoint_objects[line][(bar, 0)].get_tonal_interval(pitch)
        if mel_interval not in [-8, -4, 1, 4, 5, 8]:
            return False 
    #similarly, we want to ensure that Notes against which a Suspended Note begins will be Consonant
    if beat == 0 and line == 0 and bar in self._attempt_parameters[other_line]["suspension_bars"]:
        mel_interval = self._get_counterpoint_pitch(line, bar - 1, 2).get_tonal_interval(pitch)
        if mel_interval in [-8, 1, 8]:
            return False
        if bar == self._length - 2:
            if self._mode_resolver.is_final(self._mode_resolver.get_default_pitch_from_interval(pitch, -2)):
                if mel_interval not in [-5, -3, -2, 2, 4]:
                    return False
    return True

def prevents_cross_relation_on_simultaneous_onsets(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2 
    if (bar, beat) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar, beat)]
        if c_note is not None and isinstance(c_note, Pitch) and c_note.is_cross_relation(pitch):
            return False 
    return True

def handle_downbeats_two_part_counterpoint(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2 
    if beat == 0:
        c_note = self._get_counterpoint_pitch(other_line, bar, beat)
        if c_note is not None and isinstance(c_note, Pitch) and not self._is_consonant(c_note, pitch):
            if (bar, 0) in self._counterpoint_objects[other_line] or (bar, 2) not in self._counterpoint_objects[other_line]:
                return False 
            susp_resolve = self._counterpoint_objects[other_line][(bar, 2)]
            if ( pitch.get_tonal_interval(c_note) not in self._legal_intervals["resolvable_dissonance"] or 
                (isinstance(susp_resolve, Pitch) and c_note.get_tonal_interval(susp_resolve)) != -2 ):
                return False 
            if ( (bar, 1) in self._counterpoint_objects[other_line] and 
                c_note.get_tonal_interval(self._counterpoint_objects[other_line][(bar, 1)]) != -2 ):
                return False 
    return True

