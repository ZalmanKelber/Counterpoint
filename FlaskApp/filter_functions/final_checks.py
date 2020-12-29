import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

#makes sure that the note a step down from the high note of an ascending leap appears somewhere later in the melody
def ascending_intervals_are_filled_in(self: object) -> bool:
    for line in range(self._height):
        for i, entity in enumerate(self._counterpoint_stacks[line]):
            if isinstance(entity, Pitch) and i < len(self._counterpoint_stacks[line]) - 2: #note that we exclude the last interval
                interval = entity.get_tonal_interval(self._counterpoint_stacks[line][i + 1])
                if interval > 2:
                    filled_in = False 
                    for j in range(i + 2, len(self._counterpoint_stacks[line])):
                        if self._counterpoint_stacks[line][i + 1].get_tonal_interval(self._counterpoint_stacks[line][j]) == -2:
                            filled_in = True 
                            break 
                    if not filled_in: 
                        return False 
    return True 

#for use in Imitation Theme
def check_for_second_outline_pitch(self: object) -> bool:
    found = False 
    for index in self._all_indices[0]:
        if index[1] % 2 == 0:
            if ( self._counterpoint_objects[0][index].get_scale_degree() == self._attempt_parameters[0]["second_outline_pitch"]
                and self._counterpoint_objects[0][index].get_accidental() == Accidental.NATURAL ):
                found = True 
    return found