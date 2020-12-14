#determines whether inserted note is the highest or lowest
def _check_for_lowest_and_highest(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> None:
    if not isinstance(entity, Pitch): return 
    if entity.is_unison(self._attempt_parameters[line]["lowest"]):
        self._attempt_parameters[line]["lowest_has_been_placed"] = True 
    if entity.is_unison(self._attempt_parameters[line]["highest"]):
        self._attempt_parameters[line]["highest_has_been_placed"] = True 