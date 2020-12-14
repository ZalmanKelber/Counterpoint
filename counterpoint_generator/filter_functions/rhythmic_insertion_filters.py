#in an unaccompanied melody (as with two-part counterpoint), there are no circumstances under which we 
#don't end on a breve 
def end_on_breve(self: object, pitch: Pitch, line: int, bar: int, beat: float, durations: set[int]) -> set[int]:
    if (bar, beat) == (self._length - 1, 0):
        return { 16 }
    else: return durations