import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange


def ensure_lowest_and_highest_have_been_placed(self: object, line: int, bar: int, beat: float) -> bool:
    if not self._attempt_parameters[line]["lowest_has_been_placed"] and bar >= self._attempt_parameters[line]["lowest_must_appear_by"]:
        return False 
    if not self._attempt_parameters[line]["highest_has_been_placed"] and bar >= self._attempt_parameters[line]["highest_must_appear_by"]:
        return False 
    return True