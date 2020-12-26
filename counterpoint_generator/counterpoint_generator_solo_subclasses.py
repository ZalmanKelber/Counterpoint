import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from random import random, randint, shuffle

from abc import ABC

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange, Hexachord
from mode_resolver import ModeResolver

from counterpoint_generator import CounterpointGenerator

from counterpoint_generator_species_subclasses import FirstSpeciesCounterpointGenerator
from counterpoint_generator_species_subclasses import FifthSpeciesCounterpointGenerator
from counterpoint_generator_subclasses import SoloMelody

from filter_functions.melodic_insertion_checks import last_interval_is_descending_step
from filter_functions.melodic_insertion_checks import begin_and_end_on_mode_final
from filter_functions.melodic_insertion_checks import enforce_interval_order_strict
from filter_functions.melodic_insertion_checks import handles_interval_order_loosest
from filter_functions.melodic_insertion_checks import start_with_outline_pitch

from filter_functions.rhythmic_insertion_filters import enforce_max_long_notes_on_downbeats
from filter_functions.rhythmic_insertion_filters import end_on_breve

from filter_functions.change_parameter_checks import check_for_added_downbeat_long_note

from filter_functions.final_checks import check_for_second_outline_pitch

class CantusFirmusGenerator (FirstSpeciesCounterpointGenerator, SoloMelody):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        #Add the end by descending step optional function
        self._melodic_insertion_checks.append(last_interval_is_descending_step)
    
    #override:
    #override the generate counterpoint function to provide the option of ending by descending step
    def generate_counterpoint(self, must_end_by_descending_step: bool = False) -> None:
        #this property is referenced by the last_interval_is_descending_step insertion check to determine whether 
        #or not to enforce the rule
        self._must_end_by_descending_step = must_end_by_descending_step
        super().generate_counterpoint()

    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500:
            return True 
        return False 

class FreeMelodyGenerator (FifthSpeciesCounterpointGenerator, SoloMelody):
    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)

        self._melodic_insertion_checks.append(end_stepwise)

        self._rhythmic_insertion_filters.append(enforce_max_long_notes_on_downbeats)
    
        self._change_parameters_checks.append(check_for_added_downbeat_long_note)

    #override:
    #override the initialize function so that we can assign the max number of downbeat notes equal or longer than Whole Notes
    def _initialize(self) -> None:
        super()._initialize()
        self._assign_max_downbeat_whole_notes()

    def _assign_max_downbeat_whole_notes(self) -> None:
        self._attempt_parameters[0]["max_downbeat_long_notes"] = 0 if random() < .5 else 1
        self._attempt_parameters[0]["downbeat_long_notes_placed"] = 0

    #override:
    #collect unlimited Cantus Firmus examples within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500 or (self._number_of_backtracks > 300 and len(self._solutions) == 0):
            return True 
        return False 

class ImitationThemeGenerator (FifthSpeciesCounterpointGenerator, SoloMelody):
    def __init__(self, lines: list[VocalRange], mode: Mode, lowest: Note, highest: Note, hexachord: Hexachord):
        super().__init__(randint(3, 6), lines, mode)
        self._lowest = lowest
        self._highest = highest
        self._hexachord = hexachord

        self._melodic_insertion_checks.remove(begin_and_end_on_mode_final)
        self._melodic_insertion_checks.remove(handles_interval_order_loosest)

        self._melodic_insertion_checks.append(enforce_interval_order_strict)
        self._melodic_insertion_checks.append(start_with_outline_pitch)

        self._rhythmic_insertion_filters.remove(end_on_breve)

        self._final_checks.append(check_for_second_outline_pitch)

    #override:
    #Dotted Whole Notes should be available for any downbeat in an opening Theme
    def _get_available_durations(self, line: int, bar: int, beat: float) -> set[int]:
        if (bar, beat) == (0, 0):
            if self._length == 3:
                return { 6 }
            else:
                return { 6, 8, 12, 16 }
        elif beat == 0:
            return { 2, 4, 6, 8, 12 }
        elif beat == 2:
            return { 2, 4, 6, 8 }
        else:
            return { 2 }

    #override:
    #in the Imitation Theme, we rely on the predetermined highest and lowest notes and do not require 
    #either to appear within the theme
    def _assign_highest_and_lowest(self) -> None:
        self._attempt_parameters[0]["lowest"] = self._lowest
        self._attempt_parameters[0]["highest"] = self._highest
        self._attempt_parameters[0]["lowest_must_appear_by"] = self._length
        self._attempt_parameters[0]["highest_must_appear_by"] = self._length

        outline_pitches = self._mode_resolver.get_outline_pitches(self._hexachord)
        shuffle(outline_pitches)

        self._attempt_parameters[0]["first_outline_pitch"] = outline_pitches[0]
        self._attempt_parameters[0]["second_outline_pitch"] = outline_pitches[1]


    #override:
    #collect unlimited Themes within 3500 backtracks
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 3500 or (self._number_of_backtracks > 300 and len(self._solutions) == 0):
            return True 
        return False 