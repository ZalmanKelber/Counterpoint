import sys
sys.path.insert(0, "/Users/alexkelber/Development/midi2audio")

from midi2audio import FluidSynth

from time import time 
import math
from random import random

from notation_system import ModeOption
from cantus_firmus import CantusFirmus, GenerateCantusFirmus
from two_part_first_species import GenerateTwoPartFirstSpecies, Orientation
from two_part_second_species import GenerateTwoPartSecondSpecies
from two_part_third_species import GenerateTwoPartThirdSpecies
from two_part_fourth_species import GenerateTwoPartFourthSpecies
from midi_writer import MidiWriter

def main():
    # for mode in ModeOption:
    #     start_time = time()
    #     g2p1s = GenerateTwoPartFirstSpecies(8 + math.floor(random() * 5), mode, 5)
    #     g2p1s.generate_2p1s()
    #     print("time to generate counterpoint:", (time() - start_time) * 1000)
    #     mw = MidiWriter()
    #     mw.write_midi_from_counterpoint(g2p1s.get_optimal(), "counterpoint.mid")
    #     fs = FluidSynth("/Users/alexkelber/Development/FluidR3_GM/FluidR3_GM.sf2")
    #     fs.play_midi("counterpoint.mid")
    #     fs.midi_to_audio("counterpoint.mid", "audio/first-species-" + mode.value["name"] + ".wav")

    # for mode in ModeOption:
    #     orientation = Orientation.BELOW if random() > .5 else Orientation.ABOVE
    #     g2p2s = GenerateTwoPartSecondSpecies(8 + math.floor(random() * 5), mode, 5, orientation=orientation)
    #     g2p2s.generate_2p2s()
    #     optimal = g2p2s.get_optimal()
    #     if optimal is not None:
    #         mw = MidiWriter()
    #         mw.write_midi_from_counterpoint(optimal, "counterpoint.mid")
    #         for filename in ["FluidR3_GM/FluidR3_GM.sf2"]:
    #             print(filename)
    #             fs = FluidSynth("/Users/alexkelber/Development/" + filename)
    #             fs.play_midi("counterpoint.mid")
    #             fs.midi_to_audio("counterpoint.mid", "audio/second-species-" + mode.value["name"] + ".wav")

    # for mode in ModeOption:
    #     orientation = Orientation.BELOW if random() > .5 else Orientation.ABOVE
    #     octave = 4 if orientation == Orientation.ABOVE else 5
    #     g2p3s = GenerateTwoPartThirdSpecies(11, mode, octave, orientation=orientation)
    #     g2p3s.generate_2p3s()
    #     optimal = g2p3s.get_optimal()
    #     while optimal is None:
    #         g2p3s = GenerateTwoPartThirdSpecies(11, mode, octave, orientation=orientation)
    #         g2p3s.generate_2p3s()
    #         optimal = g2p3s.get_optimal()
    #     mw = MidiWriter()
    #     mw.write_midi_from_counterpoint(optimal, "counterpoint.mid")
    #     for filename in ["FluidR3_GM/FluidR3_GM.sf2"]:
    #         print(filename)
    #         fs = FluidSynth("/Users/alexkelber/Development/" + filename)
    #         fs.play_midi("counterpoint.mid")
    #         fs.midi_to_audio("counterpoint.mid", "audio/third-species-" + mode.value["name"] + ".wav")

    for mode in ModeOption:
        exercises = []
        g2p4s = GenerateTwoPartFourthSpecies(11, mode, 4)
        g2p4s.generate_2p4s()
        optimal = g2p4s.get_optimal()
        while optimal is None:
            g2p4s = GenerateTwoPartFourthSpecies(11, mode, 4)
            g2p4s.generate_2p4s()
            optimal = g2p4s.get_optimal()
        mw = MidiWriter()
        mw.write_midi_from_counterpoint(optimal, "counterpoint.mid")
        for filename in ["FluidR3_GM/FluidR3_GM.sf2"]:
            fs = FluidSynth("/Users/alexkelber/Development/" + filename)
            fs.play_midi("counterpoint.mid")
            fs.midi_to_audio("counterpoint.mid", "audio/fourth-species-" + mode.value["name"] + ".wav")

    
if __name__ == "__main__":
    main()
