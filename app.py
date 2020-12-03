import sys
sys.path.insert(0, "/Users/alexkelber/Development/midi2audio")

from midi2audio import FluidSynth

from time import time 
import math
from random import random

from notation_system import ModeOption
from cantus_firmus import CantusFirmus, GenerateCantusFirmus
from two_part_first_species import GenerateTwoPartFirstSpecies
from midi_writer import MidiWriter

def main():
    for mode in ModeOption:
        start_time = time()
        g2p1s = GenerateTwoPartFirstSpecies(8 + math.floor(random() * 5), mode)
        g2p1s.generate_2p1s()
        print("time to generate counterpoint:", (time() - start_time) * 1000)
        mw = MidiWriter()
        mw.write_midi_from_counterpoint(g2p1s.get_optimal(), "two-part-first-species-counterpoint.mid")
        fs = FluidSynth("/Users/alexkelber/Development/FluidR3_GM/FluidR3_GM.sf2")
        fs.play_midi("two-part-first-species-counterpoint.mid")
    
if __name__ == "__main__":
    main()
