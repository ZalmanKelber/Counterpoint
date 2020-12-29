import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver


#in an unaccompanied melody (as with two-part counterpoint), there are no circumstances under which we 
#don't end on a breve 
def end_on_breve(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if (bar, beat) == (self._length - 1, 0):
        return { 16 }
    return durations

#in the Fifth Species, we decide the max number of eighth notes that can be added
def enforce_max_pairs_of_eighths(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if self._attempt_parameters[line]["pairs_of_eighths_placed"] == self._attempt_parameters[line]["max_pairs_of_eighths"]:
        durations.discard(1)
    return durations

#in a Quarter Note Upper Neighbor (speaking purely melodically), two out of the three notes must be quarters
def upper_neighbor_cannot_occur_between_two_longer_notes(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if ( len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch) and 
        self._counterpoint_stacks[line][-2].get_duration() != 2 and self._counterpoint_stacks[line][-1].get_duration() == 2
        and self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1]) == 2 and 
        self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) == -2 ):
        return { 2 } if 2 in durations else set()
    return durations

#prevents long notes for extending over final measure
def handles_penultimate_bar(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if (bar, beat) == (self._length - 2, 0):
        durations.discard(16)
        durations.discard(12)
    if (bar, beat) == (self._length - 2, 2):
        durations.discard(8)
        durations.discard(6)
    return durations

#ensures Eighth Notes move by step
def handles_first_eighth(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        if abs(self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)) != 2:
            durations.discard(1)
    return durations

#further restriction on Eighth Note figures
def eighths_on_beat_one_preceded_by_quarter_or_in_same_direction_are_followed_by_quarter(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if len(self._counterpoint_stacks[line]) > 2 and isinstance(self._counterpoint_stacks[line][-3], Pitch):
        if beat == 2:
            if self._counterpoint_stacks[line][-3].get_duration() == 2 and self._counterpoint_stacks[line][-2].get_duration() == 1:
                return { 2 } if 2 in durations else set()
            if ( self._counterpoint_stacks[line][-3].get_tonal_interval(self._counterpoint_stacks[line][-2]) == self._counterpoint_stacks[line][-2].get_tonal_interval(self._counterpoint_stacks[line][-1])
                and self._counterpoint_stacks[line][-3].get_tonal_interval(self._counterpoint_stacks[line][-2]) == self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) ):
                return { 2 } if 2 in durations else set()
    return durations

#enforces the rule that Eighth Notes on beat "3" must be Lower Neighbors
def eighths_on_beat_three_must_be_a_step_down_from_previous_note(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        if beat == 3 and self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) != -2:
            durations.discard(1)
    return durations


#Anticipations must be followed by a Quarter Note, Half Note or Dotted Half Note
def handles_second_note_of_anticipation(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        if self._counterpoint_stacks[line][-1].is_unison(pitch):
            durations.discard(16)
            durations.discard(12)
            durations.discard(4)
    return durations

#handles case in which second note of Anticipation is Quarter Note
def anticipation_followed_by_quarter_must_be_followed_by_eighths(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if self._counterpoint_stacks[line][-2].is_unison(self._counterpoint_stacks[line][-1]) and self._counterpoint_stacks[line][-1].get_duration() == 2:
            return { 1 } if 1 in durations else set()
    return durations

#Quarter Note runs (including Eighths) cannot have more than one leap.
#Quarter Note runs ending on beat "2" cannot be followed by a Half Note if the Half Note is approached
#by ascending motion or if the length of the run is only two Quarter Notes
def regulates_quarter_runs(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if ( len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch) and 
        self._counterpoint_stacks[line][-1].get_duration() == 2 ):
        if beat == 2:
            if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) > 0:
                durations.discard(4)
            elif ( len(self._counterpoint_stacks[line]) > 2 and isinstance(self._counterpoint_stacks[line][-3], Pitch) and 
                self._counterpoint_stacks[line][-3].get_duration() != 2 and self._counterpoint_stacks[line][-2].get_duration() == 2 ):
                durations.discard(4)
        if abs(self._counterpoint_stacks[line][-1].get_tonal_interval(pitch)) > 2:
            for i in range(len(self._counterpoint_stacks[line]) - 2, -1, -1):
                if not isinstance(self._counterpoint_stacks[line][i], Pitch) or self._counterpoint_stacks[line][i].get_duration() != 2:
                    break 
                if abs(self._counterpoint_stacks[line][i].get_tonal_interval(self._counterpoint_stacks[line][i + 1])) > 2:
                    durations.discard(2)
                    break 
    return durations

#in Fifth Species, sharp notes cannot be longer than a Whole Note
def handles_sharp_durations(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if self._mode_resolver.is_sharp(pitch):
        durations.discard(16)
        durations.discard(12)
    return durations

#a Quarter Note followed by a descending leap should not be followed by a note longer than a Half Note
def handles_rhythm_after_descending_quarter_leap(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        if self._counterpoint_stacks[line][-1].get_tonal_interval(pitch) < -2 and self._counterpoint_stacks[line][-1].get_duration() == 2:
            durations.discard(16)
            durations.discard(12)
            durations.discard(8)
            durations.discard(6)
    return durations

#Breves and Quarters may not follow each other and Dotted Whole Notes may not follow Quarters
#In addition, Quarter Notes may not follow Whole Notes on downbeats
def handles_slow_fast_juxtoposition(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        if self._counterpoint_stacks[line][-1].get_duration() == 2:
            durations.discard(16)
            durations.discard(12)
        if self._counterpoint_stacks[line][-1].get_duration() == 16:
            durations.discard(2)
        if self._counterpoint_stacks[line][-1].get_duration() == 8 and beat == 0:
            durations.discard(2)
    return durations 

#if the melody doesn't begin with a Rest, it may not begin with a Quarter or Half Note (Dotted Half Notes are acceptable however)
def handles_beginning_of_fifth_species(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if (bar, beat) == (0, 0):
        durations.discard(4)
        durations.discard(2)
    return durations

#Dotted Half Notes on consecutive Downbeats aren't permissible, nor are Whole Notes on the Downbeat following a Dotted Half Note
def handles_downbeat_after_dotted_half_note(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if beat == 0 and (bar - 1, 0) in self._counterpoint_objects[line]:
        if isinstance(self._counterpoint_objects[line][(bar - 1, 0)], Pitch) and self._counterpoint_objects[line][(bar - 1, 0)].get_duration() == 6:
            durations.discard(8)
            durations.discard(6)
    return durations

#a melody in Fifth Species must end with a Whole Note or Half Note
def handles_rhythm_of_penultimate_measure(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if bar == self._length - 2:
        if beat == 0:
            return { 8 } if 8 in durations else set()
        if beat == 2:
            return { 4 } if 4 in durations else set()
    return durations

#makes melody less monotonous
def prevents_lack_of_syncopation(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if beat == 0 and all([(bar - i, 0) in self._counterpoint_objects[line] and isinstance(self._counterpoint_objects[line][(bar - i, 0)], Pitch) for i in range(1, 4)]):
        if all([self._counterpoint_objects[line][(bar - i, 0)].get_duration() >= 4 for i in range(1, 4)]):
            durations.discard(8)
            durations.discard(6)
            durations.discard(4)
    return durations

#the same syncopated pitch should not occur two measures in a row
def prevents_repeated_syncopated_pitches(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if ( beat == 2 and (bar, 0) not in self._counterpoint_objects[line] and (bar - 1, 2) in self._counterpoint_objects[line] and 
        self._counterpoint_objects[line][(bar - 1, 2)].is_unison(pitch) ):
        durations.discard(8)
        durations.discard(6)
    return durations

#prevent more than the max number of downbeat long notes from being placed (not including the final measure)
def enforce_max_long_notes_on_downbeats(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if ( bar != self._length - 1 and beat == 0 and 
        self._attempt_parameters[line]["downbeat_long_notes_placed"] == self._attempt_parameters[line]["max_downbeat_long_notes"] ):
        durations.discard(16)
        durations.discard(12)
        durations.discard(8)
    return durations

#only in multi-part examples: prevents penultimate notes that are same Scale Degree as Leading Tone but not Leading Tone
def pentultimate_note_is_leading_tone(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if bar == self._length - 2:
        if pitch.get_scale_degree() == self._mode_resolver.get_mode_leading_tone() and not self._mode_resolver.is_leading_tone(pitch):
            if beat == 0:
                durations.discard(8)
            if beat == 2:
                durations.discard(4)
    return durations

#for use in Imitation Opening
def follow_imitation_pattern_rhythm(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    imitation_index = len(self._counterpoint_stacks[line]) - self._attempt_parameters[line]["number_of_rests"]
    imitation_duration = self._counterpoint_stacks[self._starting_line][imitation_index].get_duration()
    return { imitation_duration } if imitation_duration in durations else set()




