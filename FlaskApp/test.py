import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, current_dir)

from midi2audio import FluidSynth

from time import time 
import math
from random import random, randint, shuffle

from notation_system.notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange, Hexachord
from counterpoint_generator.two_part_imitative_counterpoint import TwoPartImitativeCounterpointGenerator
from midi.midi_writer import MidiWriter
from score.lilypond_template_writer import TemplateWriter

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
