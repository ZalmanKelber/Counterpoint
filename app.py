import sys
sys.path.insert(0, "/Users/alexkelber/Development/midi2audio")

from midi2audio import FluidSynth

from time import time 
import math
from random import random, randint

from notation_system import ModeOption, RangeOption
from cantus_firmus import CantusFirmus, GenerateCantusFirmus
from two_part_first_species import GenerateTwoPartFirstSpecies, Orientation
from two_part_second_species import GenerateTwoPartSecondSpecies
from two_part_third_species import GenerateTwoPartThirdSpecies
from two_part_fourth_species import GenerateTwoPartFourthSpecies
from one_part_fifth_species import GenerateOnePartFifthSpecies
from two_part_fifth_species import GenerateTwoPartFifthSpecies
from two_part_free_counterpoint import GenerateTwoPartFreeCounterpoint
from multi_part_first_species import GenerateMultiPartFirstSpecies
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
    #     # fs.midi_to_audio("counterpoint.mid", "audio/first-species-" + mode.value["name"] + ".wav")

    # # for mode in ModeOption:
    #     # orientation = Orientation.BELOW if random() > .5 else Orientation.ABOVE
    #     # g2p2s = GenerateTwoPartSecondSpecies(8 + math.floor(random() * 5), mode, 5, orientation=orientation)
    #     # g2p2s.generate_2p2s()
    #     # optimal = g2p2s.get_optimal()
    #     # if optimal is not None:
    #     #     mw = MidiWriter()
    #     #     mw.write_midi_from_counterpoint(optimal, "counterpointçc.mid")
    #     #     for filename in ["FluidR3_GM/FluidR3_GM.sf2"]:
    #     #         print(filename)
    #     #         fs = FluidSynth("/Users/alexkelber/Development/" + filename)
    #     #         fs.play_midi("counterpoint.mid")
    #     #         fs.midi_to_audio("counterpoint.mid", "audio/second-species-" + mode.value["name"] + ".wav")

    # # for mode in ModeOption:
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
            # fs.midi_to_audio("counterpoint.mid", "audio/third-species-" + mode.value["name"] + ".wav")

    # for mode in ModeOption:
        # exercises = []
        # ornt = Orientation.BELOW if random() < .5 else Orientation.ABOVE
        # g2p4s = GenerateTwoPartFourthSpecies(11, mode, 5, orientation=ornt)
        # g2p4s.generate_2p4s()
        # optimal = g2p4s.get_optimal()
        # while optimal is None:
        #     g2p4s = GenerateTwoPartFourthSpecies(11, mode, 4)
        #     g2p4s.generate_2p4s()
        #     optimal = g2p4s.get_optimal()
        # mw = MidiWriter()
        # mw.write_midi_from_counterpoint(optimal, "counterpoint.mid")
        # for filename in ["FluidR3_GM/FluidR3_GM.sf2"]:
        #     fs = FluidSynth("/Users/alexkelber/Development/" + filename)
        #     fs.play_midi("counterpoint.mid")
            # fs.midi_to_audio("counterpoint.mid", "audio/fourth-species-" + mode.value["name"] + ".wav")

    # for mode in ModeOption:
    #     optimal = None 
    #     while optimal is None:
    #         g1p5s = GenerateOnePartFifthSpecies(randint(8, 12), mode, range_option=RangeOption.TENOR)
    #         g1p5s.generate_1p5s()
    #         optimal = g1p5s.get_optimal()
    #     if optimal is not None:
    #         mw = MidiWriter()
    #         mw.write_midi_from_counterpoint(optimal, "counterpoint.mid")
    #         for filename in ["FluidR3_GM/FluidR3_GM.sf2"]:
    #             fs = FluidSynth("/Users/alexkelber/Development/" + filename)
    #             fs.play_midi("counterpoint.mid")
    #             # fs.midi_to_audio("counterpoint.mid", "audio/fifth-species-one-part-" + mode.value["name"] + ".wav")

    # for mode in ModeOption:
    #     optimal = None 
    #     range_option = RangeOption.ALTO if mode in [ModeOption.IONIAN, ModeOption.DORIAN, ModeOption.PHRYGIAN] else RangeOption.SOPRANO
    #     while optimal is None:
    #         g2p5s = GenerateTwoPartFifthSpecies(randint(8, 11), mode, range_option=range_option)
    #         g2p5s.generate_2p5s()
    #         optimal = g2p5s.get_optimal()
    #     if optimal is not None:
    #         mw = MidiWriter()
    #         mw.write_midi_from_counterpoint(optimal, "counterpoint.mid")
    #         for filename in ["FluidR3_GM/FluidR3_GM.sf2"]:
    #             fs = FluidSynth("/Users/alexkelber/Development/" + filename)
    #             fs.play_midi("counterpoint.mid")
                # fs.midi_to_audio("counterpoint.mid", "audio/fifth-species-" + mode.value["name"] + ".wav")

    # for i in range(10, 13):
    #     for mode in ModeOption:
    #         optimal = None 
    #         while optimal is None:
    #             g2pfc = GenerateTwoPartFreeCounterpoint(randint(14, 16), mode)
    #             g2pfc.generate_2pfc()
    #             optimal = g2pfc.get_optimal()
    #         if optimal is not None:
    #             # g2pfc.print_function_log()
    #             mw = MidiWriter()
    #             mw.write_midi_from_counterpoint(optimal, "counterpoint.mid")
    #             for filename in ["FluidR3_GM/FluidR3_GM.sf2"]:
    #                 fs = FluidSynth("/Users/alexkelber/Development/" + filename)
    #                 fs.play_midi("counterpoint.mid")
    #                 fs.midi_to_audio("counterpoint.mid", "audio/free-counterpoint-" + str(i) + "-" + mode.value["name"] + ".wav")

    for mode in ModeOption:
        optimal = None 
        count = 0
        while optimal is None:
            count += 1
            gmp1s = GenerateMultiPartFirstSpecies(randint(8, 12), 5, 1, mode)
            gmp1s.generate_mp1s()
            optimal = gmp1s.get_optimal()
        if optimal is not None:
            # g2pfc.print_function_log()
            mw = MidiWriter()
            mw.write_midi_from_counterpoint(optimal, "counterpoint.mid")
            for filename in ["FluidR3_GM/FluidR3_GM.sf2"]:
                fs = FluidSynth("/Users/alexkelber/Development/" + filename)
                fs.play_midi("counterpoint.mid")
                # fs.midi_to_audio("counterpoint.mid", "audio/free-counterpoint-" + str(i) + "-" + mode.value["name"] + ".wav")


    
if __name__ == "__main__":
    main()
