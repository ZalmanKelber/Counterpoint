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