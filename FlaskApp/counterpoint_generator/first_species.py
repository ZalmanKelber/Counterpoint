from abc import ABC

from random import randint, random, shuffle
import math

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from notation_system.mode_resolver import ModeResolver

from base_class import CounterpointGenerator

from filter_functions.melodic_insertion_checks import prevent_cross_relations_on_notes_separated_by_one_other_note
from filter_functions.melodic_insertion_checks import enforce_interval_order_strict
from filter_functions.melodic_insertion_checks import prevent_dissonances_from_being_outlined
from filter_functions.melodic_insertion_checks import prevent_any_repetition_of_three_intervals
from filter_functions.melodic_insertion_checks import last_interval_of_first_species
from filter_functions.melodic_insertion_checks import prevent_highest_note_from_being_in_middle
from filter_functions.melodic_insertion_checks import melody_cannot_change_direction_three_times_in_a_row
from filter_functions.melodic_insertion_checks import prevent_three_notes_from_immediately_repeating
from filter_functions.melodic_insertion_checks import pitch_cannot_appear_three_times_in_six_notes

from filter_functions.final_checks import ascending_intervals_are_filled_in

class FirstSpeciesCounterpointGenerator (CounterpointGenerator, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        #First Species has fairly strict melodic requirements in addition to the default ones
        self._melodic_insertion_checks.append(prevent_cross_relations_on_notes_separated_by_one_other_note)
        self._melodic_insertion_checks.append(enforce_interval_order_strict)
        self._melodic_insertion_checks.append(prevent_dissonances_from_being_outlined)
        self._melodic_insertion_checks.append(prevent_any_repetition_of_three_intervals)
        self._melodic_insertion_checks.append(prevent_highest_note_from_being_in_middle)
        self._melodic_insertion_checks.append(last_interval_of_first_species)
        self._melodic_insertion_checks.append(melody_cannot_change_direction_three_times_in_a_row)
        self._melodic_insertion_checks.append(prevent_three_notes_from_immediately_repeating)
        self._melodic_insertion_checks.append(pitch_cannot_appear_three_times_in_six_notes)

        self._final_checks.append(ascending_intervals_are_filled_in)

    #override:
    #override the get_available_durations, which is extremely simple in First Species
    def _get_available_durations(self, line: int, bar: int, beat: float) -> set[int]:
        return { 16 } if bar == self._length - 1 else { 8 }

    #override:
    #override the rest durations function, since rests aren't used in First Species
    def _get_valid_rest_durations(self, line: int, bar: int, beat: float) -> set[int]:
        return set()

    #override:
    #in First Species, outside of the highest and lowest notes and leading tones, we don't want any sharp notes
    def _delineate_vocal_ranges(self) -> None:
        super()._delineate_vocal_ranges()
        for line in range(self._height):
            self._attempt_parameters[line]["available_pitches"] = list(filter(self._remove_sharp_pitches, self._attempt_parameters[line]["available_pitches"]))

    #helper function for the above that filters out the pitches we don't want in First Species
    def _remove_sharp_pitches(self, pitch: Pitch) -> bool:
        if self._mode_resolver.is_sharp(pitch) and not self._mode_resolver.is_leading_tone(pitch):
            return False 
        return True

    #override:
    #override the function that assigns the highest and lowest intervals
    #a First Species exercise should have a range between a fifth and octave, should include
    #the mode final on a note that is not the highest pitch, and the lowest and highest note should not form a diminished fifth 
    def _assign_highest_and_lowest(self) -> None:
        for line in range(self._height):
            vocal_range = self._lines[line]
            final = self._mode_resolver.get_default_mode_final(vocal_range)
            #choose a range interval between a fifth and an octave and choose a highest and lowest note such that the 
            #default mode final is within the range and not the top note
            range_size = randint(5, 8)
            highest = self._mode_resolver.get_default_pitch_from_interval(final, randint(2, range_size))
            lowest = self._mode_resolver.get_default_pitch_from_interval(highest, range_size * -1)
            top_leeway = highest.get_tonal_interval(self._mode_resolver.get_highest_of_range(vocal_range))
            bottom_leeway = self._mode_resolver.get_lowest_of_range(vocal_range).get_tonal_interval(lowest)
            #if we've exceeded the bounds of the vocal range, adjust the highest and lowest up or down accordingly.
            #this is guaranteed to still keep our default mode final within the range
            if top_leeway < 0:
                highest = self._mode_resolver.get_default_pitch_from_interval(highest, top_leeway)
                lowest = self._mode_resolver.get_default_pitch_from_interval(lowest, top_leeway)
            if bottom_leeway < 0:
                highest = self._mode_resolver.get_default_pitch_from_interval(highest, bottom_leeway * -1)
                lowest = self._mode_resolver.get_default_pitch_from_interval(lowest, bottom_leeway * -1)
            #check to see if the top and bottom notes create a tritone, in which case we extend the top or bottom
            #note by one (which will stay within each designated vocal range, since a tritone will only form between B and F)
            if lowest.get_chromatic_interval(highest) == 6:
                if random() < .5:
                    highest = self._mode_resolver.get_default_pitch_from_interval(highest, 2)
                else:
                    lowest = self._mode_resolver.get_default_pitch_from_interval(lowest, -2)

            self._attempt_parameters[line]["lowest"] = lowest
            self._attempt_parameters[line]["highest"] = highest

            self._attempt_parameters[line]["lowest_must_appear_by"] = randint(3, self._length - 1)
            self._attempt_parameters[line]["highest_must_appear_by"] = randint(3, self._length - 1)

