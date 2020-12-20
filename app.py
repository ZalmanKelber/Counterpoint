import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/midi")
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/counterpoint_generator")
sys.path.insert(0, "/Users/alexkelber/Development/midi2audio")

from midi2audio import FluidSynth

from time import time 
import math
from random import random, randint, shuffle

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from two_part_first_species import TwoPartFirstSpeciesGenerator
from midi_writer import MidiWriter

def main():
    for mode in [Mode.IONIAN]:
        optimal = None
        while optimal is None:
            # print(vocal_range.value, mode.value)
            tp1s = TwoPartFirstSpeciesGenerator(randint(8, 12), [VocalRange.ALTO, VocalRange.TENOR], mode)
            tp1s.generate_counterpoint()
            tp1s.score_solutions()
            optimal = tp1s.get_one_solution()
        if optimal is not None:
            mw = MidiWriter()
            mw.write_midi_from_counterpoint(optimal, "counterpoint.mid")
            fs = FluidSynth("/Users/alexkelber/Development/FluidR3_GM/FluidR3_GM.sf2")
            fs.play_midi("counterpoint.mid")

if __name__ == "__main__":
    main()
