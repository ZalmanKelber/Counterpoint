import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/midi")
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/score")
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/counterpoint_generator")
sys.path.insert(0, "/Users/alexkelber/Development/midi2audio")

from midi2audio import FluidSynth

from time import time 
import math
from random import random, randint, shuffle

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange, Hexachord
from two_part_counterpoint import TwoPartImitativeCounterpointGenerator
from midi_writer import MidiWriter
from lilypond_template_writer import TemplateWriter

def main():
    for mode in [Mode.DORIAN]:
        for h in range(1):
            lines = [VocalRange.ALTO, VocalRange.SOPRANO]
            optimal = None
            while optimal is None:
                counterpoint_generator = TwoPartImitativeCounterpointGenerator(randint(14, 16), lines, mode)
                counterpoint_generator.generate_counterpoint()
                counterpoint_generator.score_solutions()
                optimal = counterpoint_generator.get_one_solution()
                if optimal is not None:
                    counterpoint_generator.print_counterpoint()
            if optimal is not None:
                mw = MidiWriter()
                mw.write_midi_from_counterpoint(optimal, "counterpoint.mid", speed_up=1) 
                fs = FluidSynth("/Users/alexkelber/Development/FluidR3_GM/FluidR3_GM.sf2")
                fs.play_midi("counterpoint.mid")
                tw = TemplateWriter()
                tw.write_template_from_counterpoint(optimal, lines, "counterpoint.ly")

if __name__ == "__main__":
    main()
