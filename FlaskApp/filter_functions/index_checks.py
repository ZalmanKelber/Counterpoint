import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver


def ensure_lowest_and_highest_have_been_placed(self: object, line: int, bar: int, beat: float) -> bool:
    if not self._attempt_parameters[line]["lowest_has_been_placed"] and bar >= self._attempt_parameters[line]["lowest_must_appear_by"]:
        return False 
    if not self._attempt_parameters[line]["highest_has_been_placed"] and bar >= self._attempt_parameters[line]["highest_must_appear_by"]:
        return False 
    return True