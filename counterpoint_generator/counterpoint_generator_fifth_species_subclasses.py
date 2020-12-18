import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")

from random import random

from abc import ABC

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from mode_resolver import ModeResolver

from counterpoint_generator import CounterpointGenerator

from counterpoint_generator_species_subclasses import FifthSpeciesCounterpointGenerator
from counterpoint_generator_subclasses import TwoPartCounterpoint

class TwoPartFifthSpeciesGenerator (FifthSpeciesCounterpointGenerator, TwoPartCounterpoint):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)