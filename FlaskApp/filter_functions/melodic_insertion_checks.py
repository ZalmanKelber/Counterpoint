import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

############# added to CounterpointGenerator (base class) ################

#ensures that all adjacent notes move by melodically legal intervals
def valid_melodic_interval(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        (t_interval, c_interval) = self._counterpoint_stacks[line][-1].get_intervals(pitch)
        if t_interval not in self._legal_intervals["tonal_adjacent_melodic"]: return False 
        if c_interval not in self._legal_intervals["chromatic_adjacent_melodic"]: return False
        if (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"]: return False
        #in addition, leaps are not allowed between notes that are either sharp or leading tones
        if abs(t_interval) > 2:
            if ( (self._mode_resolver.is_sharp(self._counterpoint_stacks[line][-1]) or self._mode_resolver.is_leading_tone(self._counterpoint_stacks[line][-1])) 
                and (self._mode_resolver.is_sharp(pitch) or self._mode_resolver.is_leading_tone(pitch)) ):
                return False
    return True 

#ensures that any melodic ascending leap of a minor sixth is followed by a descending half-step
def ascending_minor_sixths_are_followed_by_descending_half_step(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if self._counterpoint_stacks[line][-2].get_chromatic_interval(self._counterpoint_stacks[line][-1]) == 8:
            if self._counterpoint_stacks[line][-1].get_chromatic_interval(pitch) != -1:
                return False
    return True 

#ensures that the highest note appears only once 
def prevent_highest_duplicates(self, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if self._attempt_parameters[line]["highest_has_been_placed"] and pitch.is_unison(self._attempt_parameters[line]["highest"]):
        return False 
    return True 

#prevents the same two notes from being immediately repeated (regardless of rhythm).  e.g. D -> F -> D -> F
def prevent_two_notes_from_immediately_repeating(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 2 and isinstance(self._counterpoint_stacks[line][-3], Pitch):
        if ( self._counterpoint_stacks[line][-3].is_unison(self._counterpoint_stacks[line][-1]) and 
            self._counterpoint_stacks[line][-2].is_unison(pitch) ):
            if ( self._counterpoint_stacks[line][-3].get_duration() == self._counterpoint_stacks[line][-2].get_duration()
                and self._counterpoint_stacks[line][-2].get_duration() == self._counterpoint_stacks[line][-1].get_duration() ):
                return False 
    return True 

#same as above but with three notes
def prevent_three_notes_from_immediately_repeating(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 4 and isinstance(self._counterpoint_stacks[line][-5], Pitch):
        if ( self._counterpoint_stacks[line][-5].is_unison(self._counterpoint_stacks[line][-2]) and 
            self._counterpoint_stacks[line][-4].is_unison(self._counterpoint_stacks[line][-1]) and
            self._counterpoint_stacks[line][-3].is_unison(pitch) ):
            return False 
    return True 


################# added to subclasses that specify number of lines ####################

#in an unaccompanied melody, we must begin and end on the same note, which must be the mode final
def begin_and_end_on_mode_final(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if (bar, beat) == (0, 0):
        return self._mode_resolver.is_final(pitch)
    if (bar, beat) == (self._length - 1, 0):
        return pitch.is_unison(self._counterpoint_objects[line][(0, 0)])
    return True

################ added to subclasses that specify species ######################

#prevents highest note from occuring in the direct middle of a line with an odd number of measures
#used in species 1 - 4
def prevent_highest_note_from_being_in_middle(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if self._length % 2 == 1 and (bar, beat) == (self._length // 2, 0):
        if pitch.is_unison(self._attempt_parameters[line]["highest"]): 
            return False 
    return True 

def prevent_cross_relations_on_notes_separated_by_one_other_note(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if self._counterpoint_stacks[line][-2].is_cross_relation(pitch): 
            return False 
    return True 

#in ascending motion, successive "tonal intervals" must be the same or smaller.
#in descending motion, succesive "tonal intervals" must be the same or larger 
def enforce_interval_order_strict(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        prev_interval = self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1])
        cur_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
        if cur_interval > prev_interval and not (cur_interval > 0 and prev_interval < 0):
            return False 
    return True 

#a dissonance can be "outlined" in two ways: by two notes separated by intervals that are all either ascending or descending 
#and that are followed / succeeded by intervals in the opposite direction (or are endpoints of the melody).
#or between any two notes separated by intervals that are all leaps of a third or greater
def prevent_dissonances_from_being_outlined(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    #begin by checking whether or not the current note marks the end of a segment of ascending or 
    #descending motion -- either by moving in the contrary direction or by being the end of the piece
    segment_start_pitch, segment_end_pitch, i, is_ascending = None, None, None, None
    if bar == self._length - 1: 
        prev_interval = self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1])
        cur_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
        if (prev_interval > 0 and cur_interval > 0) or (prev_interval < 0 and cur_interval < 0):
            segment_end_pitch = pitch 
            is_ascending = cur_interval > 0
            i = len(self._counterpoint_stacks[line]) - 2
        else:
            segment_end_pitch = self._counterpoint_stacks[line][-1]
            is_ascending = prev_interval > 0
            i = i = len(self._counterpoint_stacks[line]) - 3
    elif len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        prev_interval = self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1])
        cur_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
        if (prev_interval > 0 and cur_interval < 0) or (prev_interval < 0 and cur_interval > 0):
            segment_end_pitch = self._counterpoint_stacks[line][-1]
            is_ascending = prev_interval > 0
            i = i = len(self._counterpoint_stacks[line]) - 3
    if segment_end_pitch is not None:
        while i >= 0 and isinstance(self._counterpoint_stacks[line][i], Pitch):
            prev_interval = self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1])
            if ( (prev_interval < 0 and is_ascending) or (prev_interval > 0 and not is_ascending) 
                or i == 0 or not isinstance(self._counterpoint_stacks[line][i - 1], Pitch)):
                segment_start_pitch = self._counterpoint_stacks[line][i + 1]
                break
            i -= 1
        #now detemine whether the segment ends form a forbidden dissonance
        if segment_start_pitch is not None:
            (t_interval, c_interval) = segment_start_pitch.get_intervals(segment_end_pitch)
            if ( t_interval not in self._legal_intervals["tonal_outline_melodic"] or 
                c_interval not in self._legal_intervals["chromatic_outline_melodic"] or 
                (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
                return False 

    #now determine how many pitches are connected to the current pitch by intervals that are all 
    #leaps and check each one
    pitches_to_check = []
    i = len(self._counterpoint_stacks[line]) - 1
    while i >= 0 and isinstance(self._counterpoint_stacks[line][i], Pitch):
        interval = self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1] if i < len(self._counterpoint_stacks[line]) - 1 else pitch)
        if abs(interval) > 2:
            pitches_to_check.append(self._counterpoint_stacks[line][i])
        else:
            break
        i -= 1
    for pitch_to_check in pitches_to_check:
        (t_interval, c_interval) = pitch_to_check.get_intervals(pitch)
        if ( t_interval not in self._legal_intervals["tonal_outline_melodic"] or 
            c_interval not in self._legal_intervals["chromatic_outline_melodic"] or 
            (t_interval, c_interval) in self._legal_intervals["forbidden_combinations"] ):
            return False 
    return True 

#prevents any four note pattern from repeating (e.g. C -> E -> F -> D ... E -> G -> A -> F)
def prevent_any_repetition_of_three_intervals(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 2 and isinstance(self._counterpoint_stacks[line][-3], Pitch):
        interval_chain = [
            self._counterpoint_stacks[line][-3].get_tonal_interval(self._counterpoint_stacks[line][-2]),
            self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]),
            self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
        ]
        for i in range(len(self._counterpoint_stacks[line]) - 5):
            if isinstance(self._counterpoint_stacks[line][i], Pitch):
                prev_interval_chain = [
                    self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1]),
                    self._counterpoint_stacks[line][i + 1].get_tonal_interval(self._counterpoint_stacks[line][i + 2]),
                    self._counterpoint_stacks[line][i + 2].get_tonal_interval(self._counterpoint_stacks[line][i + 3])
                ]
                if prev_interval_chain == interval_chain:
                    return False 
    return True 

#prevents melody from sounding monotonous
def pitch_cannot_appear_three_times_in_six_notes(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        pitches_to_check = [self._counterpoint_stacks[line][-1]]
        i = len(self._counterpoint_stacks[line]) - 2
        #collect up to five of the most recent pitches
        while i >= max(len(self._counterpoint_stacks[line]) - 5, 0) and isinstance(self._counterpoint_stacks[line][i], Pitch):
            pitches_to_check.append(self._counterpoint_stacks[line][i])
            i -= 1
        num_unisons = 0
        for pitch_to_check in pitches_to_check:
            if pitch_to_check.is_unison(pitch):
                num_unisons += 1
                if num_unisons == 2:
                    return False 
    return True

#prevents  melody from sounding monotonous
def melody_cannot_change_direction_three_times_in_a_row(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 3 and isinstance(self._counterpoint_stacks[line][-4], Pitch):
        interval1 = self._counterpoint_stacks[line][-4].get_tonal_interval(self._counterpoint_stacks[line][-3])
        interval2 = self._counterpoint_stacks[line][-3].get_tonal_interval(self._counterpoint_stacks[line][-2])
        interval3 = self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1])
        interval4 = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
        if interval1 > 0 and interval2 < 0 and interval3 > 0 and interval4 < 0:
            return False 
        if interval1 < 0 and interval2 > 0 and interval3 < 0 and interval4 > 0:
            return False 
    return True

#in first species, a line must end either by step or in an ascending leap of a fourth or fifth
def last_interval_of_first_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if bar != self._length - 1:
        return True 
    if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) not in [-2, 2, 4, 5]:
        return False 
    return True

#used in certain Cantus Firmus examples
def last_interval_is_descending_step(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if not self._must_end_by_descending_step or bar != self._length - 1:
        return True 
    if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != -2:
        return False 
    return True

#interval order is handles more loosely in the Fifth Species, but the rules are accordingly more complex, as detailed in the logic below
def handles_interval_order_loosest(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        potential_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
        if potential_interval >= 3:
            if self._counterpoint_stacks[line][-1].get_duration() == 2:
                if self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) > 0:
                    return False
            for i in range(len(self._counterpoint_stacks[line]) - 2, -1, -1):
                if i <= 0 or not isinstance(self._counterpoint_stacks[line][i], Pitch): break
                interval = self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1])
                if interval < 0: break
                if interval > 2: return False 
        if potential_interval == 2:
            segment_has_leap = False
            for i in range(len(self._counterpoint_stacks[line]) - 2, -1, -1):
                if not isinstance(self._counterpoint_stacks[line][i], Pitch): break
                interval = self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1])
                if interval < 0: break
                if segment_has_leap: return False 
                segment_has_leap = interval > 2
        if potential_interval == -2:
            segment_has_leap = False
            for i in range(len(self._counterpoint_stacks[line]) - 2, -1, -1):
                if not isinstance(self._counterpoint_stacks[line][i], Pitch): break
                interval = self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1])
                if interval > 0: break
                if segment_has_leap or interval == -8: return False 
                segment_has_leap = interval < -2
        if potential_interval <= -3:
            for i in range(len(self._counterpoint_stacks[line]) - 2, -1, -1):
                if not isinstance(self._counterpoint_stacks[line][i], Pitch): break
                interval = self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1])
                if interval > 0: break
                if interval < -2: return False 
    return True 

#handles nearby augmented and diminished intervals in cases not covered by outline dissonances   
#the specific scenarios are outlined in the logic below 
def handles_other_nearby_augs_and_dims(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if self._counterpoint_stacks[line][-2].is_cross_relation(pitch): 
            return False 
        if self._counterpoint_stacks[line][-2].get_duration() != 2: 
            return True 
        (t_interval, c_interval) = self._counterpoint_stacks[line][-2].get_intervals(pitch)
        if (abs(t_interval) != 2 or abs(c_interval) != 3) and (abs(t_interval) != 3 or abs(c_interval) != 2):
            return True 
        else:
            return False 
    return True 
    
#makes sure that all sharp notes are resolved upwards by the first onset of the following measure at the latest
def sharp_notes_resolve_upwards(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if beat == 0 or (beat == 2 and (bar, 0) not in self._counterpoint_objects[line]):
        indices_to_check = [(bar - 1, 0), (bar - 1, 1), (bar - 1, 2), (bar - 1, 3)]
        pitches_to_check = []
        for index_to_check in indices_to_check:
            if index_to_check in self._counterpoint_objects[line] and isinstance(self._counterpoint_objects[line][index_to_check], Pitch):
                pitches_to_check.append(self._counterpoint_objects[line][index_to_check])
        for i, pitch_to_check in enumerate(pitches_to_check):
            if self._mode_resolver.is_sharp(pitch_to_check):
                resolved = False 
                for j in range(i + 1, len(pitches_to_check)):
                    if pitch_to_check.get_chromatic_interval(pitches_to_check[j]) == 1:
                        resolved = True 
                if not resolved and pitch_to_check.get_chromatic_interval(pitch) != 1:
                    return False 
    return True 

#in the Third and Fifth Species, ascending leaps cannot occur from accented to unaccented Quarter Note Beats
def prevents_ascending_leaps_to_weak_quarters(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if beat % 2 == 1 and len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) > 2:
            return False 
    return True 

#a descending Quarter Note leap should be followed either by a step up of by a leap up to a note within a step of the first pitch
def handles_descending_quarter_leaps(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if ( self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) < -2 and 
            self._counterpoint_stacks[line][-1].get_duration() == 2 and 
            self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != 2 and 
            abs(self._counterpoint_stacks[line][-2].get_tonal_interval(pitch)) > 2 ):
            return False 
    return True 

#repetition is only allowed after an Anticipation on beat "1"
def handles_anticipation(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if self._counterpoint_stacks[line][-1].is_unison(pitch):
            if ( beat != 2 or self._counterpoint_stacks[line][-1].get_duration() != 2 or 
                self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) != -2 ):
                return False 
    return True 

#an Anticipation must resolve downwards by step
def handles_resolution_of_anticipation(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if ( self._counterpoint_stacks[line][-2].is_unison(self._counterpoint_stacks[line][-1]) and 
            self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != -2 ):
            return False 
    return True

#in the Fifth Species, we specify the number of melodic octaves permissible in a given line
def enforce_max_melodic_octaves(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        if ( abs(self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)) == 8 and 
            self._attempt_parameters[line]["melodic_octaves_placed"] == self._attempt_parameters[line]["max_melodic_octaves"] ):
            return False 
    return True

#places further restrictions on quarters between two leaps
def handles_quarter_between_two_leaps(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch) and self._counterpoint_stacks[line][-1].get_duration() == 2:
        prev_interval = self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1])
        cur_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
        if prev_interval > 2 and cur_interval < -2:
            return False 
        if prev_interval == -8 and cur_interval == 8:
            return False 
    return True

#octaves should be preceded and followed by contrary motion
def octaves_surrounded_by_contrary_motion(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        prev_interval = self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1])
        cur_interval = self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)
        if prev_interval == 8 and cur_interval > 0: 
            return False
        if prev_interval == -8 and cur_interval < 0:
            return False 
        if prev_interval > 0 and cur_interval == 8:
            return False 
        if prev_interval < 0 and cur_interval == -8:
            return False 
    return True

#ensures Eighth Notes are followed by stepwise motion
def eighths_move_stepwise(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        if self._counterpoint_stacks[line][-1].get_duration() == 1 and abs(self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)) != 2:
            return False 
    return True

#further Eighth Notes restriction
def eighths_leading_to_downbeat_must_be_lower_neighbor(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        if beat == 0 and self._counterpoint_stacks[line][-1].get_duration() == 1 and self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != 2:
            return False 
        elif beat == 3.5 and self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != -2:
            return False
    return True

#further Eighth Notes restriction
def eighths_in_same_direction_must_be_followed_by_motion_in_opposite_direction(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 3 and isinstance(self._counterpoint_stacks[line][-4], Pitch):
        if self._counterpoint_stacks[line][-3].get_duration() == 1 and self._counterpoint_stacks[line][-2].get_duration() == 1:
            if ( self._counterpoint_stacks[line][-4].get_tonal_interval(self._counterpoint_stacks[line][-3]) == self._counterpoint_stacks[line][-3].get_tonal_interval(self._counterpoint_stacks[line][-2]) 
                and self._counterpoint_stacks[line][-4].get_tonal_interval(self._counterpoint_stacks[line][-3]) == self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) ):
                if ( (self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) > 0 and self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) > 0) or 
                    (self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) < 0 and self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) < 0) ):
                    return False 
    return True 


#for almost all case scenarios for highest voice
def end_stepwise(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if bar == self._length - 1 and abs(self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)) != 2:
        return False 
    return True 

#does not include anticipations.  C -> D -> C -> B -> C is illegal but D -> C -> C -> B -> C is legal
#for use in Fifth Species
def prevent_note_from_repeating_three_times_in_five_notes(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if bar != self._length - 1:
        if len(self._counterpoint_stacks[line]) > 3 and isinstance(self._counterpoint_stacks[line][-4], Pitch):
            if self._counterpoint_stacks[line][-4].is_unison(pitch) and self._counterpoint_stacks[line][-2].is_unison(pitch):
                return False 
    return True

#prevents figures of the form F# -> E -> G
def prevents_fifteenth_century_sharp_resolution(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if ( self._mode_resolver.is_sharp(self._counterpoint_stacks[line][-2]) and 
            self._counterpoint_stacks[line][-2].get_chromatic_interval(pitch) == 1 and 
            self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) == -2 ):
            return False 
    return True

#in the Second Species, we need to check notes on successive downbeats
def prevents_repetition_second_species(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if beat == 0:
        if (bar - 1, 0) in self._counterpoint_objects[line] and isinstance(self._counterpoint_objects[line][(bar - 1, 0)], Pitch):
            if self._counterpoint_objects[line][(bar - 1, 0)].is_unison(pitch):
                return False 
        if (bar - 3, 0) in self._counterpoint_objects[line] and isinstance(self._counterpoint_objects[line][(bar - 3, 0)], Pitch):
            if ( self._counterpoint_objects[line][(bar - 2, 0)].is_unison(pitch) and 
                self._counterpoint_objects[line][(bar - 3, 0)].is_unison(self._counterpoint_objects[line][(bar - 1, 0)]) ):
                return False 
    return True 

#in Two-part polyphony, we want to end on a cadence
def begin_and_end_two_part_counterpoint(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    other_line = (line + 1) % 2
    if bar == self._length - 1:
        return self._mode_resolver.is_final(pitch)
    if len(self._counterpoint_stacks[line]) == 0 or not isinstance(self._counterpoint_stacks[line][-1], Pitch):
        c_note = self._counterpoint_objects[other_line][(0, 0)]
        if c_note is not None and isinstance(c_note, Pitch):
            return self._mode_resolver.is_final(pitch) or self._mode_resolver.is_final(self._mode_resolver.get_default_pitch_from_interval(pitch, 4))
        else:
            return self._mode_resolver.is_final(pitch)
    return True

#in Two-part polyphony, we want to end on a cadence (and this must be through contrary motion)
def penultimate_bar_two_part_counterpoint(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if (bar, beat) == (self._length - 2, 0):
        if ( self._mode_resolver.is_final(self._mode_resolver.get_default_pitch_from_interval(pitch, -2)) 
            or (self._mode_resolver.is_final(self._mode_resolver.get_default_pitch_from_interval(pitch, 4)) and 
            self._mode != Mode.PHRYGIAN) ):
            return True
        return False 
    if (bar, beat) == (self._length - 1, 0) and self._counterpoint_stacks[line][-1].get_duration() == 8:
        if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) > 0:
            return False 
    return True

#prevents melody from sounding "stuck"
def goes_up_after_third_appearance_of_note(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        pitch_to_check = self._counterpoint_stacks[line][-1]
        if pitch_to_check.get_tonal_interval(pitch) < 0:
            num_unisons = 0
            for i in range(len(self._counterpoint_stacks[line]) - 2, -1, -1):
                if not isinstance(self._counterpoint_stacks[line][i], Pitch):
                    break
                if pitch_to_check.get_tonal_interval(self._counterpoint_stacks[line][i]) > 0:
                    break
                if self._counterpoint_stacks[line][i].is_unison(pitch_to_check):
                    num_unisons += 1
                    if num_unisons == 2:
                        return False 
    return True

#for use in Imitative Themes
def start_with_outline_pitch(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if (bar, beat) == (0, 0):
        if ( pitch.get_scale_degree() != self._attempt_parameters[line]["first_outline_pitch"]
            or pitch.get_accidental() != Accidental.NATURAL ):
            return False 
    return True

#for use in Imitation Opening
def follow_imitation_pattern(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    imitation_index = len(self._counterpoint_stacks[line]) - self._attempt_parameters[line]["number_of_rests"]
    imitation_pitch = self._counterpoint_stacks[self._starting_line][imitation_index]
    if imitation_pitch.get_tonal_interval(pitch) != self._translation_interval:
        return False 
    if not self._mode_resolver.is_sharp(imitation_pitch) and self._mode_resolver.is_sharp(pitch):
        return False
    if self._mode_resolver.is_sharp(imitation_pitch) and not self._mode_resolver.is_sharp(pitch):
        if ( pitch.get_scale_degree() in [1, 4, 5] or (pitch.get_scale_degree() == 2 and self._mode == Mode.AEOLIAN)
            or pitch.get_scale_degree() == 7 and self._mode in [Mode.DORIAN, Mode.LYDIAN] ):
            return False 
    return True