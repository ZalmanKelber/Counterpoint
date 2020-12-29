import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

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

#register when we add a downbeat note longer or equal to a Whole Note
def check_for_added_downbeat_long_note(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> None:
    if bar != self._length - 1 and beat == 0 and isinstance(entity, Pitch) and entity.get_duration() >= 8:
        self._attempt_parameters[line]["downbeat_long_notes_placed"] += 1

#keep track of the number of Rests
def add_rest(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> None:
    if isinstance(entity, Rest):
        self._attempt_parameters[line]["number_of_rests"] += 1
