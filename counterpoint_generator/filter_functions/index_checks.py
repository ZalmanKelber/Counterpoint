def _ensure_lowest_and_highest_have_been_placed(self: object, line: int, bar: int, beat: float) -> bool:
    if not self._attempt_parameters[line]["lowest_has_been_placed"] and bar >= self._attempt_parameters[line]["lowest_must_appear_by"]:
        return False 
    if not self._attempt_parameters[line]["highest_has_been_placed"] and bar >= self._attempt_parameters[line]["highest_must_appear_by"]:
        return False 