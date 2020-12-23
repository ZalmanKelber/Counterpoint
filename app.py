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
from two_part_counterpoint import TwoPartCounterpointGenerator
from midi_writer import MidiWriter

def main():
    for mode in Mode:
        for i in range(2):
            optimal = None
            while optimal is None:
                two_part_counterpoint_generator = TwoPartCounterpointGenerator(randint(12, 16), [VocalRange.ALTO, VocalRange.SOPRANO], mode)
                two_part_counterpoint_generator.generate_counterpoint()
                two_part_counterpoint_generator.score_solutions()
                optimal = two_part_counterpoint_generator.get_one_solution()
            if optimal is not None:
                mw = MidiWriter()
                mw.write_midi_from_counterpoint(optimal, "counterpoint.mid", speed_up=1)
                fs = FluidSynth("/Users/alexkelber/Development/FluidR3_GM/FluidR3_GM.sf2")
                fs.play_midi("counterpoint.mid")

if __name__ == "__main__":
    main()
