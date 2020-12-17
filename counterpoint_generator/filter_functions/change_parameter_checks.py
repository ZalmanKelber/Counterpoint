import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange

#determines whether inserted note is the highest or lowest
def check_for_lowest_and_highest(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> None:
    if not isinstance(entity, Pitch): return 
    if entity.is_unison(self._attempt_parameters[line]["lowest"]):
        self._attempt_parameters[line]["lowest_has_been_placed"] = True 
    if entity.is_unison(self._attempt_parameters[line]["highest"]):
        self._attempt_parameters[line]["highest_has_been_placed"] = True 


#note that we only register the pair of eighth notes once the second eighth has been added
def check_for_added_eigth_note_pair(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> None:
    if beat % 2 == 1.5:
        self._attempt_parameters[line]["pairs_of_eighths_placed"] += 1

#register when we add a melodic octave
def check_for_added_melodic_octave(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> None:
    if ( isinstance(entity, Pitch) and len(self._counterpoint_stacks[line]) > 1 and 
        isinstance(self._counterpoint_stacks[line][-2], Pitch) and 
        abs(self._counterpoint_stacks[line][-2].get_tonal_interval(entity)) == 8 ):
        self._attempt_parameters[line]["melodic_octaves_placed"] += 1