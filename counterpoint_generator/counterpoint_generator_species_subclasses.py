from counterpoint_generator import CounterpointGenerator

from filter_functions.melodic_insertion_checks import prevent_cross_relations_on_notes_separated_by_one_other_note
from filter_functions.melodic_insertion_checks import enforce_interval_order_strict
from filter_functions.melodic_insertion_checks import prevent_dissonances_from_being_outlined
from filter_functions.melodic_insertion_checks import prevent_any_repetition_of_three_intervals


class FirstSpeciesCounterpointGenerator (CounterpointGenerator, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(self, length, lines, mode)

        #First Species has fairly strict melodic requirements in addition to the default ones
        self._melodic_insertion_checks.append(prevent_cross_relations_on_notes_separated_by_one_other_note)
        self._melodic_insertion_checks.append(enforce_interval_order_strict)
        self._melodic_insertion_checks.append(prevent_dissonances_from_being_outlined)
        self._melodic_insertion_checks.append(prevent_any_repetition_of_three_intervals)

    #override:
    #override the get_valid_durations, which is extremely simple in First Species
    def _get_valid_durations(self, pitch: Pitch, line: int, bar: int, beat: float) -> set[int]:
        return { 16 } if bar == self._length - 1 else { 8 }

    #override:
    #override the rest durations function, since rests aren't used in First Species
    def _get_valid_rest_durations(self, line: int, bar: int, beat: float) -> set[int]:
        return set()

    #override:
    #override the function that assigns the highest and lowest intervals
    #a First Species exercise should have a range between a fifth and octave, should include
    #the mode final on a note that is not the highest pitch, and the lowest and highest note should not form a diminished fifth 
    def _assign_highest_and_lowest(self) -> None:
        for line in range(self._height):
            vocal_range = self._lines[line]
            


            self._attempt_parameters[line]["lowest"] = self._mode_resolver.get_lowest_of_range(vocal_range)
            self._attempt_parameters[line]["highest"] = self._mode_resolver.get_highest_of_range(vocal_range)
            self._attempt_parameters[line]["lowest_must_appear_by"] = self._length - 1
            self._attempt_parameters[line]["highest_must_appear_by"] = self._length - 1

