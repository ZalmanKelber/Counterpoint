from time import time 

from notation_system import ModeOption
from cantus_firmus import CantusFirmus, GenerateCantusFirmus

start_time = time()
gcf1 = GenerateCantusFirmus(8, ModeOption.DORIAN)
gcf2 = GenerateCantusFirmus(11, ModeOption.PHRYGIAN)
gcf3 = GenerateCantusFirmus(8, ModeOption.IONIAN, octave = 3)
for gcf in [gcf1, gcf2, gcf3]:
    cf = gcf.generate_cf()
    cf.print_cf()
print("program runtime:", (time() - start_time) * 1000)