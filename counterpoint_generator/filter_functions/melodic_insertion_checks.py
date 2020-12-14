
############# added to CounterpointGenerator (base class) ################

#ensures that all adjacent notes move by melodically legal intervals
def valid_melodic_interval(self: object, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
        (t_interval, c_interval) = self._counterpoint_stacks[line][-1].get_intervals(pitch)
        if t_interval not in self._legal_intervals["tonal_adjacent_melodic"]: return False 
        if c_interval not in self._legal_intervals["chromatic_outline_melodic"]: return False
        if (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"]: return False
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
def prevent_two_notes_from_immediately_repeating(self, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 2 and isinstance(self._counterpoint_stacks[line][-3], Pitch):
        if ( self._counterpoint_stacks[line][-3].is_unison(self._counterpoint_stacks[line][-1]) and 
            self._counterpoint_stacks[line][-2].is_unison(pitch) ):
            return False 
    return True 


################# added to subclasses that specify number of lines ####################

#in an unaccompanied melody, we must begin and end on the same note, which must be the mode final
def begin_and_end_on_mode_final(self, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if (bar, beat) == (0, 0):
        return self._mode_resolver.is_final(pitch)
    if (bar, beat) == (self._length - 1, 0):
        return pitch.is_unison(self._counterpoint_objects[line][(0, 0)])

################ added to subclasses that specify species ######################

def prevent_cross_relations_on_notes_separated_by_one_other_note(self, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
    if len(self._counterpoint_stacks[line]) > 1 and isinstance(self._counterpoint_stacks[line][-2], Pitch):
        if self._counterpoint_stacks[line][-2].is_cross_relation(pitch): 
            return False 
    return True 
