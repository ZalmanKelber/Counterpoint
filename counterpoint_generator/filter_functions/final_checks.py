import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange

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