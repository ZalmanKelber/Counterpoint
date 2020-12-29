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

from multiple_lines import MultipleLines

from filter_functions.rhythmic_insertion_filters import end_on_breve

from filter_functions.harmonic_insertion_checks import prevents_hidden_fifths_and_octaves_two_part
from filter_functions.harmonic_insertion_checks import no_dissonant_onsets_on_downbeats
from filter_functions.harmonic_insertion_checks import start_and_end_intervals_two_part
from filter_functions.harmonic_insertion_checks import prevents_large_leaps_in_same_direction
from filter_functions.harmonic_insertion_checks import prevents_diagonal_cross_relations
from filter_functions.harmonic_insertion_checks import prevents_landini

from filter_functions.score_functions import penalize_perfect_intervals_on_downbeats

class TwoLines (MultipleLines, ABC):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        if len(lines) != 2:
            raise Exception("Two-part Counterpoint must have two lines")
        super().__init__(length, lines, mode)

        self._rhythmic_insertion_filters.append(end_on_breve)

        self._harmonic_insertion_checks.append(prevents_hidden_fifths_and_octaves_two_part)
        self._harmonic_insertion_checks.append(no_dissonant_onsets_on_downbeats)
        self._harmonic_insertion_checks.append(start_and_end_intervals_two_part)
        self._harmonic_insertion_checks.append(prevents_large_leaps_in_same_direction)
        self._harmonic_insertion_checks.append(prevents_diagonal_cross_relations)
        self._harmonic_insertion_checks.append(prevents_landini)

        self._score_functions.append(penalize_perfect_intervals_on_downbeats)