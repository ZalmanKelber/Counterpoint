import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

#checks that Suspension Note is Consonant on onset and forms a Resolvable Dissonance on following Downbeat
def form_suspension_fourth_species(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat == 2 and (bar + 1, 0) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar, 0)]
        if not self._is_consonant(c_note, pitch):
            durations.discard(8)
        else:
            c_next_note = self._counterpoint_objects[other_line][(bar + 1, 0)]
            if c_next_note is not None:
                if not self._is_consonant(c_next_note, pitch):
                    if t_interval not in self._legal_intervals["resolvable_dissonance"]:
                        durations.discard(8)
            
    return durations

#also makes sure that the second Downbeat of a Breve is a Consonant
def prepares_suspensions_fifth_species(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat % 2 == 0 and bar < self._length - 1:
        c_note = self._get_counterpoint_pitch(other_line, bar + 1, 0)
        if c_note is not None:
            if not self._is_consonant(c_note, pitch):
                durations.discard(16)
                if c_note.get_tonal_interval(pitch) not in self._legal_intervals["resolvable_dissonance"]:
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
            if not self._is_consonant(c_note, pitch):
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

def handles_weak_half_note_dissonance_in_other_line(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat == 0 and (bar, 2) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar, 2)]
        if c_note is not None:
            if not self._is_consonant(c_note, pitch):
                if c_note.get_duration() not in [2, 4]:
                    durations.discard(16)
                    durations.discard(12)
                    durations.discard(8)
                    durations.discard(6)
                    return durations
                prev_interval = self._get_counterpoint_pitch(other_line, bar, 1).get_tonal_interval(c_note)
                if abs(prev_interval) != 2 or (prev_interval == 2 and c_note.get_duration() == 2):
                    durations.discard(16)
                    durations.discard(12)
                    durations.discard(8)
                    durations.discard(6)
                    return durations
                next_index = (bar, 3) if (bar, 3) in self._counterpoint_objects[other_line] else (bar + 1, 0)
                next_interval = c_note.get_tonal_interval(self._counterpoint_objects[other_line][next_index])
                if next_interval != prev_interval:
                    durations.discard(16)
                    durations.discard(12)
                    durations.discard(8)
                    durations.discard(6)
                    return durations
                if c_note.get_duration() == 2:
                    if not self._is_consonant(self._counterpoint_objects[other_line][next_index], pitch):
                        durations.discard(8)
    if beat == 0 and (bar + 1, 2) in self._counterpoint_objects[other_line]:
        c_note = self._counterpoint_objects[other_line][(bar + 1, 2)]
        if c_note is not None:
            if not self._is_consonant(c_note, pitch):
                if c_note.get_duration() not in [2, 4]:
                    durations.discard(16)
                    return durations
                prev_interval = self._get_counterpoint_pitch(other_line, bar + 1, 1).get_tonal_interval(c_note)
                if abs(prev_interval) != 2 or (prev_interval == 2 and c_note.get_duration() == 2):
                    durations.discard(16)
                    return durations
                next_index = (bar + 1, 3) if (bar + 1, 3) in self._counterpoint_objects[other_line] else (bar + 2, 0)
                next_interval = c_note.get_tonal_interval(self._counterpoint_objects[other_line][next_index])
                if next_interval != prev_interval:
                    durations.discard(16)
                    return durations
                if c_note.get_duration() == 2:
                    if not self._is_consonant(self._counterpoint_objects[other_line][next_index], pitch):
                        durations.discard(8)
    return durations


############ helper functions ##############

def handles_weak_quarter_note_dissonance_in_other_line(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    other_line = (line + 1) % 2
    if beat % 1 == 0:
        index0 = (bar, beat)
        #check for weak Quarter Note dissonance on beat
        if beat % 2 == 1:
            if index0 in self._counterpoint_objects[other_line] and improperly_handled_dissonance(self, pitch, index0, other_line):
                return set()
        #check for weak Quarter Note dissonance on next beat
        else:
            index1 = (bar, beat + 1)
            if ( index1 in self._counterpoint_objects[other_line] and 
                (improperly_handled_dissonance(self, pitch, index1, other_line) or is_dissonant(self, pitch, index0, other_line)) ):
                return { 2 } if 2 in durations else set()
            index2 = (bar, 2) if beat == 0 else (bar + 1, 0)
            if index1 in self._counterpoint_objects[other_line] and is_dissonant(self, pitch, index2, other_line):
                if beat == 0 or self._counterpoint_objects[other_line][index2].get_tonal_interval(pitch) not in self._legal_intervals["resolvable_dissonance"]:
                    durations.discard(8)
                    durations.discard(6)
                    return durations 
            # #check for weak Quarter Note dissonance in three beats
            index3 = (bar, 3) if beat == 0 else (bar + 1, 1)
            if ( index3 in self._counterpoint_objects[other_line] and 
                improperly_handled_dissonance(self, pitch, index3, other_line) ):
                durations.discard(8)
                durations.discard(6)
    return durations

def improperly_handled_dissonance(self: object, pitch: Pitch, index: tuple[int, int], line: int) -> bool:
    c_note = self._counterpoint_objects[line][index]
    if not isinstance(c_note, Pitch): 
        return False 
    if not self._is_consonant(c_note, pitch):
        (bar, beat) = index
        prev_c_note = self._get_counterpoint_pitch(line, bar, beat - 1)
        next_c_note = self._counterpoint_objects[line][(bar, beat + 1) if beat < 3 else (bar + 1, 0)]
        if (prev_c_note.get_tonal_interval(c_note), c_note.get_tonal_interval(next_c_note)) not in [(-2, 2), (-2, -2), (2, 2), (2, -2), (-2, -3)]:
            return True 
        if (prev_c_note.get_tonal_interval(c_note), c_note.get_tonal_interval(next_c_note)) == (-2, -3):
            camb_tail_index = (bar + 1, 0) if beat == 1 else (bar + 1, 2)
            camb_intermediary_index = (bar, 3) if beat == 1 else (bar + 1, 1)
            if camb_tail_index not in self._counterpoint_objects[line]:
                return True 
            camb_tail = self._counterpoint_objects[line][camb_tail_index]
            if isinstance(camb_tail, Pitch):
                if camb_intermediary_index not in self._counterpoint_objects[line]:
                    return next_c_note.get_tonal_interval(camb_tail) != 2
                camb_intermediary = self._counterpoint_objects[line][camb_intermediary_index]
                if isinstance(camb_intermediary, Pitch):
                    return next_c_note.get_tonal_interval(camb_intermediary) != 2 or camb_intermediary.get_tonal_interval(camb_tail) != 2
    return False 

def is_dissonant(self: object, pitch: Pitch, index: tuple[int, int], line: int) -> bool:
    c_note = self._get_counterpoint_pitch(line, index[0], index[1])
    if c_note is None: 
        return False 
    (t_interval, c_interval) = c_note.get_intervals(pitch)
    if ( abs(t_interval) % 7 not in self._legal_intervals["tonal_harmonic_consonant"] 
        or abs(c_interval) % 12 not in self._legal_intervals["chromatic_harmonic_consonant"] 
        or (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"] ):
        return True 
    return False

    
        


