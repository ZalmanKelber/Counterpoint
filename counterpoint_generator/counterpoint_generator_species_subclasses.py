import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from random import randint, random

from abc import ABC

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from mode_resolver import ModeResolver

from counterpoint_generator import CounterpointGenerator

from filter_functions.melodic_insertion_checks import prevent_cross_relations_on_notes_separated_by_one_other_note
from filter_functions.melodic_insertion_checks import enforce_interval_order_strict
from filter_functions.melodic_insertion_checks import prevent_dissonances_from_being_outlined
from filter_functions.melodic_insertion_checks import prevent_any_repetition_of_three_intervals
from filter_functions.melodic_insertion_checks import last_interval_of_first_species
from filter_functions.melodic_insertion_checks import prevent_highest_note_from_being_in_middle
from filter_functions.melodic_insertion_checks import melody_cannot_change_direction_three_times_in_a_row
from filter_functions.melodic_insertion_checks import prevent_three_notes_from_immediately_repeating
from filter_functions.melodic_insertion_checks import pitch_cannot_appear_three_times_in_six_notes

from filter_functions.melodic_insertion_checks import end_stepwise
from filter_functions.melodic_insertion_checks import prevents_repetition_second_species

from filter_functions.melodic_insertion_checks import handles_interval_order_loosest
from filter_functions.melodic_insertion_checks import handles_other_nearby_augs_and_dims
from filter_functions.melodic_insertion_checks import sharp_notes_resolve_upwards
from filter_functions.melodic_insertion_checks import prevents_ascending_leaps_to_weak_quarters
from filter_functions.melodic_insertion_checks import handles_descending_quarter_leaps
from filter_functions.melodic_insertion_checks import handles_anticipation
from filter_functions.melodic_insertion_checks import handles_resolution_of_anticipation
from filter_functions.melodic_insertion_checks import enforce_max_melodic_octaves
from filter_functions.melodic_insertion_checks import handles_quarter_between_two_leaps
from filter_functions.melodic_insertion_checks import octaves_surrounded_by_contrary_motion
from filter_functions.melodic_insertion_checks import eighths_move_stepwise
from filter_functions.melodic_insertion_checks import eighths_leading_to_downbeat_must_be_lower_neighbor
from filter_functions.melodic_insertion_checks import eighths_in_same_direction_must_be_followed_by_motion_in_opposite_direction
from filter_functions.melodic_insertion_checks import prevent_note_from_repeating_three_times_in_five_notes
from filter_functions.melodic_insertion_checks import prevents_fifteenth_century_sharp_resolution

from filter_functions.rhythmic_insertion_filters import enforce_max_pairs_of_eighths
from filter_functions.rhythmic_insertion_filters import upper_neighbor_cannot_occur_between_two_longer_notes
from filter_functions.rhythmic_insertion_filters import handles_first_eighth
from filter_functions.rhythmic_insertion_filters import eighths_on_beat_one_preceded_by_quarter_or_in_same_direction_are_followed_by_quarter
from filter_functions.rhythmic_insertion_filters import eighths_on_beat_three_must_be_a_step_down_from_previous_note
from filter_functions.rhythmic_insertion_filters import handles_second_note_of_anticipation
from filter_functions.rhythmic_insertion_filters import anticipation_followed_by_quarter_must_be_followed_by_eighths
from filter_functions.rhythmic_insertion_filters import regulates_quarter_runs
from filter_functions.rhythmic_insertion_filters import handles_sharp_durations
from filter_functions.rhythmic_insertion_filters import handles_rhythm_after_descending_quarter_leap
from filter_functions.rhythmic_insertion_filters import handles_slow_fast_juxtoposition
from filter_functions.rhythmic_insertion_filters import handles_beginning_of_fifth_species
from filter_functions.rhythmic_insertion_filters import handles_downbeat_after_dotted_half_note
from filter_functions.rhythmic_insertion_filters import handles_rhythm_of_penultimate_measure
from filter_functions.rhythmic_insertion_filters import prevents_lack_of_syncopation
from filter_functions.rhythmic_insertion_filters import prevents_repeated_syncopated_pitches

from filter_functions.change_parameter_checks import check_for_added_eigth_note_pair
from filter_functions.change_parameter_checks import check_for_added_melodic_octave

from filter_functions.score_functions import prioritize_long_quarter_note_runs
from filter_functions.score_functions import penalize_two_note_quarter_runs
from filter_functions.score_functions import select_ideal_ties

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

class SecondSpeciesCounterpointGenerator (CounterpointGenerator, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        self._melodic_insertion_checks.append(prevent_cross_relations_on_notes_separated_by_one_other_note)
        self._melodic_insertion_checks.append(enforce_interval_order_strict)
        self._melodic_insertion_checks.append(prevent_dissonances_from_being_outlined)
        self._melodic_insertion_checks.append(prevent_any_repetition_of_three_intervals)
        self._melodic_insertion_checks.append(prevent_highest_note_from_being_in_middle)
        self._melodic_insertion_checks.append(end_stepwise)
        self._melodic_insertion_checks.append(sharp_notes_resolve_upwards)
        self._melodic_insertion_checks.append(melody_cannot_change_direction_three_times_in_a_row)
        self._melodic_insertion_checks.append(prevent_three_notes_from_immediately_repeating)
        self._melodic_insertion_checks.append(pitch_cannot_appear_three_times_in_six_notes)
        self._melodic_insertion_checks.append(prevents_repetition_second_species)
        self._melodic_insertion_checks.append(prevents_fifteenth_century_sharp_resolution)

    #override:
    #override the get_available_durations, which consists entirely of Half Notes in the Second Speices except the penultimate measure
    #note that we rely on the base class for the _get_valid_rests method
    def _get_available_durations(self, line: int, bar: int, beat: float) -> set[int]:
        if bar == self._length - 1:
            return { 16 }
        elif (bar, beat) == (self._length - 2, 0):
            return { 4, 8}
        else:
            return { 4 }


    #override:
    #override the function that assigns the highest and lowest intervals
    #a First Species exercise should have a range between a fifth and octave, should include
    #the mode final on a note that is not the highest pitch, and the lowest and highest note should not form a diminished fifth 
    def _assign_highest_and_lowest(self) -> None:
        for line in range(self._height):
            vocal_range = self._lines[line]
            #choose a range interval between a seventh and tenth and choose a highest and lowest note
            range_size = randint(7, 10)
            range_bottom = self._mode_resolver.get_lowest_of_range(vocal_range)

            self._attempt_parameters[line]["lowest"] = self._mode_resolver.get_default_pitch_from_interval(range_bottom, randint(1, 13 - range_size))
            self._attempt_parameters[line]["highest"] = self._mode_resolver.get_default_pitch_from_interval(self._attempt_parameters[line]["lowest"], range_size)

            self._attempt_parameters[line]["lowest_must_appear_by"] = randint(3, self._length - 1)
            self._attempt_parameters[line]["highest_must_appear_by"] = randint(3, self._length - 1)

class ThirdSpeciesCounterpointGenerator (CounterpointGenerator, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        self._melodic_insertion_checks.append(prevent_cross_relations_on_notes_separated_by_one_other_note)
        self._melodic_insertion_checks.append(enforce_interval_order_strict)
        self._melodic_insertion_checks.append(prevent_dissonances_from_being_outlined)
        self._melodic_insertion_checks.append(prevent_highest_note_from_being_in_middle)
        self._melodic_insertion_checks.append(end_stepwise)
        self._melodic_insertion_checks.append(sharp_notes_resolve_upwards)
        self._melodic_insertion_checks.append(melody_cannot_change_direction_three_times_in_a_row)
        self._melodic_insertion_checks.append(prevent_three_notes_from_immediately_repeating)
        self._melodic_insertion_checks.append(pitch_cannot_appear_three_times_in_six_notes)
        self._melodic_insertion_checks.append(prevents_fifteenth_century_sharp_resolution)
        self._melodic_insertion_checks.append(prevents_ascending_leaps_to_weak_quarters)
        self._melodic_insertion_checks.append(octaves_surrounded_by_contrary_motion)

    #override:
    #override the get_available_durations, which consists entirely of Quarter Notes in the Third Speices except the penultimate measure
    #note that we rely on the base class for the _get_valid_rests method
    def _get_available_durations(self, line: int, bar: int, beat: float) -> set[int]:
        if bar == self._length - 1:
            return { 16 }
        elif (bar, beat) == (self._length - 2, 0):
            return { 2, 8 }
        else:
            return { 2 }


    #override:
    #override the function that assigns the highest and lowest intervals
    #a First Species exercise should have a range between a fifth and octave, should include
    #the mode final on a note that is not the highest pitch, and the lowest and highest note should not form a diminished fifth 
    def _assign_highest_and_lowest(self) -> None:
        for line in range(self._height):
            vocal_range = self._lines[line]
            #choose a range interval between a seventh and tenth and choose a highest and lowest note
            range_size = randint(7, 10)
            range_bottom = self._mode_resolver.get_lowest_of_range(vocal_range)

            self._attempt_parameters[line]["lowest"] = self._mode_resolver.get_default_pitch_from_interval(range_bottom, randint(1, 13 - range_size))
            self._attempt_parameters[line]["highest"] = self._mode_resolver.get_default_pitch_from_interval(self._attempt_parameters[line]["lowest"], range_size)

            self._attempt_parameters[line]["lowest_must_appear_by"] = randint(3, self._length - 1)
            self._attempt_parameters[line]["highest_must_appear_by"] = randint(3, self._length - 1)

class FifthSpeciesCounterpointGenerator (CounterpointGenerator, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)


        #melody rules for the Fifth Species are in some ways laxer but also more complex than earlier Species

            #inherited from base class:
            #valid_melodic_interval
            #ascending_minor_sixths_are_followed_by_descending_half_step
            #prevent_highest_duplicates
            #prevent_two_notes_from_immediately_repeating

        self._melodic_insertion_checks.append(handles_interval_order_loosest)
        self._melodic_insertion_checks.append(handles_other_nearby_augs_and_dims)
        self._melodic_insertion_checks.append(prevent_dissonances_from_being_outlined)
        self._melodic_insertion_checks.append(sharp_notes_resolve_upwards)
        self._melodic_insertion_checks.append(prevents_ascending_leaps_to_weak_quarters)
        self._melodic_insertion_checks.append(handles_descending_quarter_leaps)
        self._melodic_insertion_checks.append(handles_anticipation)
        self._melodic_insertion_checks.append(handles_resolution_of_anticipation)
        self._melodic_insertion_checks.append(enforce_max_melodic_octaves)
        self._melodic_insertion_checks.append(handles_quarter_between_two_leaps)
        self._melodic_insertion_checks.append(octaves_surrounded_by_contrary_motion)
        self._melodic_insertion_checks.append(eighths_move_stepwise)
        self._melodic_insertion_checks.append(eighths_leading_to_downbeat_must_be_lower_neighbor)
        self._melodic_insertion_checks.append(eighths_in_same_direction_must_be_followed_by_motion_in_opposite_direction)
        self._melodic_insertion_checks.append(prevent_note_from_repeating_three_times_in_five_notes)
        self._melodic_insertion_checks.append(prevents_fifteenth_century_sharp_resolution)

            #inherited from base class:
            #(none)

        self._rhythmic_insertion_filters.append(enforce_max_pairs_of_eighths)
        self._rhythmic_insertion_filters.append(upper_neighbor_cannot_occur_between_two_longer_notes)
        self._rhythmic_insertion_filters.append(handles_first_eighth)
        self._rhythmic_insertion_filters.append(eighths_on_beat_one_preceded_by_quarter_or_in_same_direction_are_followed_by_quarter)
        self._rhythmic_insertion_filters.append(eighths_on_beat_three_must_be_a_step_down_from_previous_note)
        self._rhythmic_insertion_filters.append(handles_second_note_of_anticipation)
        self._rhythmic_insertion_filters.append(anticipation_followed_by_quarter_must_be_followed_by_eighths)
        self._rhythmic_insertion_filters.append(regulates_quarter_runs)
        self._rhythmic_insertion_filters.append(handles_sharp_durations)
        self._rhythmic_insertion_filters.append(handles_rhythm_after_descending_quarter_leap)
        self._rhythmic_insertion_filters.append(handles_slow_fast_juxtoposition)
        self._rhythmic_insertion_filters.append(handles_beginning_of_fifth_species)
        self._rhythmic_insertion_filters.append(handles_downbeat_after_dotted_half_note)
        self._rhythmic_insertion_filters.append(handles_rhythm_of_penultimate_measure)
        self._rhythmic_insertion_filters.append(prevents_lack_of_syncopation)
        self._rhythmic_insertion_filters.append(prevents_repeated_syncopated_pitches)

            #inherited from base class:
            #check_for_lowest_and_highest

        self._change_parameters_checks.append(check_for_added_eigth_note_pair)
        self._change_parameters_checks.append(check_for_added_melodic_octave)

            #inherited from base class:
            #prioritize_stepwise_motion
            #ascending_leaps_followed_by_descending_steps

        self._score_functions.append(prioritize_long_quarter_note_runs)
        self._score_functions.append(penalize_two_note_quarter_runs)
        self._score_functions.append(select_ideal_ties)
        
        #melodic unisons are available in the Fifth Species
        self._legal_intervals["tonal_adjacent_melodic"].add(1)
        self._legal_intervals["chromatic_adjacent_melodic"].add(0)

        #in the Fifth Species, the rules for which intervals we may outline are laxer
        self._legal_intervals["tonal_outline_melodic"] = { -12, -11, -10, -9. -8, -7, -6, -5, -4, -3, -2, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 }
        self._legal_intervals["chromatic_outline_melodic"] = { -19, -17, -16, -15, -14, -13, -12, -11, -10, -9, -8, -7, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19 }

    #override:
    #override the initialize function so that we can assign the number of eighth notes and number of melodic octaves we deem permissible beforehand
    def _initialize(self) -> None:
        super()._initialize()
        self._assign_max_pairs_of_eighths()
        self._assign_max_melodic_octaves()

    def _assign_max_pairs_of_eighths(self) -> None:
        for line in range(self._height):
            chance = random()
            if chance < .05:
                self._attempt_parameters[line]["max_pairs_of_eighths"] = 2
            elif chance < .3:
                self._attempt_parameters[line]["max_pairs_of_eighths"] = 1
            else:
                self._attempt_parameters[line]["max_pairs_of_eighths"] = 0
        self._attempt_parameters[line]["pairs_of_eighths_placed"] = 0

    #limit prevents melody from becoming too choppy
    def _assign_max_melodic_octaves(self) -> None:
        for line in range(self._height):
            self._attempt_parameters[line]["max_melodic_octaves"] = 1 if random() < .6 else 2
            self._attempt_parameters[line]["melodic_octaves_placed"] = 0


    #override:
    #override the function that assigns the highest and lowest intervals
    #a Fifth Species melody should have a range between an octave and a tenth.
    #note that we don't need to worry about making sure the mode final is within the range since a range of an ovtave or greater
    #will guarantee at least one instance of the mode final to be within the available pitches
    def _assign_highest_and_lowest(self) -> None:
        for line in range(self._height):
            vocal_range = self._lines[line]
            #choose a range interval between an octave and tenth that is within each voice range
            range_size = randint(8, 10)
            leeway = 13 - range_size #this is the interval that we can add to the range_size interval to get the interval from the lowest to highest note available in the vocal range
            from_bottom = randint(1, leeway)

            self._attempt_parameters[line]["lowest"] = self._mode_resolver.get_default_pitch_from_interval(self._mode_resolver.get_lowest_of_range(vocal_range), from_bottom)
            self._attempt_parameters[line]["highest"] = self._mode_resolver.get_default_pitch_from_interval(self._attempt_parameters[line]["lowest"], range_size)

            self._attempt_parameters[line]["lowest_must_appear_by"] = randint(3, self._length - 1)
            self._attempt_parameters[line]["highest_must_appear_by"] = randint(3, self._length - 1)

    

