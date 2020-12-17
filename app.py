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
from counterpoint_generator_solo_subclasses import CantusFirmusGenerator
from midi_writer import MidiWriter

def main():
    for mode in Mode:
        for vocal_range in VocalRange:
            optimal = None
            while optimal is None:
                print(vocal_range.value, mode.value)
                cfg = CantusFirmusGenerator(randint(8, 11), [vocal_range], mode)
                cfg.generate_counterpoint()
                cfg.score_solutions()
                optimal = cfg.get_one_solution()
                print("number of solutions:", len(cfg.get_all_solutions()))
            if optimal is not None:
                mw = MidiWriter()
                mw.write_midi_from_counterpoint(optimal, "counterpoint.mid", 2.0)
                fs = FluidSynth("/Users/alexkelber/Development/FluidR3_GM/FluidR3_GM.sf2")
                fs.play_midi("counterpoint.mid")

if __name__ == "__main__":
    main()
