from time import time 

from notation_system import ModeOption
from cantus_firmus import CantusFirmus, GenerateCantusFirmus
from two_part_first_species import GenerateTwoPartFirstSpecies
from midi_writer import MidiWriter

def main():
    # start_time = time()
    # gcf1 = GenerateCantusFirmus(8, ModeOption.IONIAN)
    # gcf2 = GenerateCantusFirmus(11, ModeOption.DORIAN)
    # gcf3 = GenerateCantusFirmus(8, ModeOption.PHRYGIAN, octave = 3)
    # gcf4 = GenerateCantusFirmus(8, ModeOption.LYDIAN)
    # gcf5 = GenerateCantusFirmus(11, ModeOption.MIXOLYDIAN)
    # gcf6 = GenerateCantusFirmus(8, ModeOption.AEOLIAN, octave = 3)
    # for gcf in [gcf1, gcf2, gcf3, gcf4, gcf5, gcf6]:
    #     cf = gcf.generate_cf()
    #     cf.print_cf()
    # print("program runtime:", (time() - start_time) * 1000)
    start_time = time()
    g2p1s = GenerateTwoPartFirstSpecies(11, ModeOption.DORIAN)
    g2p1s.generate_2p1s()
    best = g2p1s.get_optimal()
    worst = g2p1s.get_worst()
    mw = MidiWriter()
    mw.write_midi_from_counterpoint(best, "two-part-first-species-counterpoint-best.mid")
    mw.write_midi_from_counterpoint(worst, "two-part-first-species-counterpoint-worst.mid")
    print("program runtime:", (time() - start_time) * 1000)
    
   

if __name__ == "__main__":
    main()
