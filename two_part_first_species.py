from random import random, shuffle
import math
from enum import Enum 

from notation_system import ModeOption, ScaleOption, Note, ModeResolver 
from cantus_firmus import CantusFirmus, GenerateCantusFirmus

#intervals it is permissible to move directly to
VALID_MELODIC_INTERVALS_CHROMATIC = { -12, -7, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 7, 8, 12 }
#intervals it is permissible to outline
CONSONANT_MELODIC_INTERVALS_CHROMATIC = { -12, -9, -8 -7, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7, 8, 9, 12 }
#intervals it is permissible to move directly to, as scale degrees
VALID_MELODIC_INTERVALS_SCALE_DEGREES = { -8, -5, -4, -3, -2, 2, 3, 4, 5, 6, 8 }
#consonant harmonic intervals
CONSONANT_HARMONIC_INTERVALS_CHROMATIC = { -12, -9, -8, -7, -5, -4, -3, 0, 3, 4, 5, 7, 8, 9, 12 }
#illegal combinations of sdg intervals and chromatic intervals that result in augmented or diminished intervals 
#respectively: cross relations, augmented seconds, diminished thirds, diminished fourths, augmented fifths and augmented sixths
FORBIDDEN_INTERVAL_COMBINATIONS = { (1, 1), (2, 3), (3, 2), (4, 5), (5, 8), (6, 10) }

#use indices to generate random mode
MODES_BY_INDEX = [ModeOption.IONIAN, ModeOption.DORIAN, ModeOption.PHRYGIAN, ModeOption.LYDIAN, ModeOption.MIXOLYDIAN, ModeOption.AEOLIAN ]

#get possible melodic intervals from final to lowest note based on interval from final to highest note
GET_POSSIBLE_INTERVALS_TO_LOWEST = {
    2: [-6, -5, -4],
    3: [-5, -4, -3],
    4: [-5, -4, -3, -2],
    5: [-4, -3, -2, 1],
    6: [-2, 1],
    8: [1]
}

#this is the average proportion of intervals that are steps in Jeppesen's Cantus Firmus examples
AVERAGE_STEPS_PERCENTAGE = .712

class Orientation (Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"

class GenerateTwoPartFirstSpecies:

    def __init__(self, length: int = None, mode: ModeOption = None, octave: int = 4, orientation: Orientation = Orientation.ABOVE):
        self._orientation = orientation
        self._mode = mode or MODES_BY_INDEX[math.floor(random() * 6)]
        self._length = length or 8 + math.floor(random() * 5) #todo: replace with normal distribution
        self._octave = octave
        self._mr = ModeResolver(self._mode)
        gcf = GenerateCantusFirmus(self._length, self._mode, self._octave)
        self._cf = None 
        #if the Cantus Firmus doesn't generate, we have to try again
        #also, if we are below the Cantus Firmus, the Cantus Firmus must end stepwise
        while self._cf is None or (self._cf.get_note(self._length - 2).get_scale_degree_interval(self._cf.get_note(self._length - 1)) < -2 and orientation == Orientation.BELOW):
            self._cf = gcf.generate_cf()

    def generate_2p1s(self):
        self._solutions = []
        self._initialize()
        # self._backtrack()

    #create the list we will backtrack through, find first, last, highest and lowest notes
    def _initialize(self):
        starting_interval_candidates = [5, 8] if self._orientation == Orientation.ABOVE else [-8]
        cf_first = self._cf.get_note(0)
        cf_second = self._cf.get_note(1)
        cf_penult = self._cf.get_note(self._length - 2)
        cf_last = self._cf.get_note(self._length - 1)
        cf_first_interval = cf_first.get_scale_degree_interval(cf_second)
        cf_last_interval = cf_penult.get_scale_degree_interval(cf_last)
        cf_highest = self._cf.get_highest_note()
        cf_lowest = self._cf.get_lowest_note()
        if self._orientation == Orientation.BELOW:
            if cf_first_interval > 0 and cf_last_interval < 0 and cf_first.get_scale_degree_interval(cf_lowest) >= -2:
                starting_interval_candidates.append(1)
        else: 
            if cf_first_interval < 0 and cf_first.get_scale_degree_interval(cf_highest) <= 2: 
                starting_interval_candidates.append(1)
        starting_interval = starting_interval_candidates[math.floor(random() * len(starting_interval_candidates))]
        ending_interval = None
        end_to_penult_interval = None
        if self._orientation == Orientation.BELOW:
            ending_interval = starting_interval
        else: 
            ending_interval_candidates = []
            if cf_last_interval == 5:
                ending_interval_candidates = [5]
            elif cf_last_interval == 4 or cf_last_interval == 2:
                ending_interval_candidates = [starting_interval] if starting_interval != 5 else [1, 8]
            else:
                ending_interval_candidates = [5] if starting_interval == 1 else [5, 8]
            ending_interval = ending_interval_candidates[math.floor(random() * len(ending_interval_candidates))]
        if Orientation == Orientation.BELOW:
            end_to_penult_interval = cf_last_interval
        else:
            if cf_last_interval == 4:
                end_to_penult_interval = 2 if random() > .5 else -2
            elif cf_last_interval > 0:
                end_to_penult_interval = 2
            elif random() > .85 and ending_interval == 8 and self._mode.value["most_common"] == 4:
                end_to_penult_interval = -5
            else:
                end_to_penult_interval = -2
        first_note = self._get_default_note_from_interval(cf_first, starting_interval)
        last_note = self._get_default_note_from_interval(cf_last, ending_interval)
        penult_note = self._get_default_note_from_interval(last_note, end_to_penult_interval)
        range_so_far = max(max(abs(first_note.get_scale_degree_interval(last_note)), abs(first_note.get_scale_degree_interval(penult_note))), abs(penult_note.get_scale_degree_interval(last_note)))
        #find lowest note so far
        lowest_so_far = first_note if (starting_interval < ending_interval and end_to_penult_interval > -5) else last_note if end_to_penult_interval > 0 else penult_note
        #get possible lowest notes 
        lowest_note_candidates = [lowest_so_far]
        for i in range(8 - range_so_far):
            candidate = self._get_default_note_from_interval(lowest_so_far, (i + 1) * -1)
            if candidate is not None and self._valid_outline(first_note, candidate) and self._valid_outline(last_note, candidate):
                if self._orientation == Orientation.BELOW or cf_highest.get_scale_degree_interval(candidate) >= -3:
                    lowest_note_candidates.append(candidate)
        lowest_note = lowest_note_candidates[math.floor(random() * len(lowest_note_candidates))]
        range_so_far += lowest_note.get_scale_degree_interval(lowest_so_far) - 1
        #find highest note so far
        highest_so_far = first_note if starting_interval > ending_interval else penult_note if end_to_penult_interval > 0 else last_note
        #get possible highest notes
        highest_note_candidates = [highest_so_far] if (starting_interval > ending_interval or end_to_penult_interval > 0) and range_so_far >= 5 else []
        for i in range(max(5 - range_so_far, 0), 8 - range_so_far):
            candidate = self._get_default_note_from_interval(highest_so_far, i + 1)
            if candidate is not None and self._valid_range(lowest_note, candidate) and self._valid_outline(first_note, candidate) and self._valid_outline(last_note, candidate):
                if self._orientation == Orientation.ABOVE or cf_lowest.get_scale_degree_interval(candidate) <= -3:
                    highest_note_candidates.append(candidate)
        highest_note = highest_note_candidates[math.floor(random() * len(highest_note_candidates))]
        print("MODE = ", self._mode.value["name"])
        print("CANTUS FIRMUS:")
        self._cf.print_cf()
        print("first note:", first_note)
        print("penultimate note:", penult_note)
        print("last note:", last_note)
        print("highest note:", highest_note)
        print("lowest note:", lowest_note)

    def _valid_adjacent(self, note1: Note, note2: Note) -> bool:
        chro_interval = note1.get_chromatic_interval(note2)
        sdg_interval = note1.get_scale_degree_interval(note2)
        if chro_interval in VALID_MELODIC_INTERVALS_CHROMATIC and (abs(sdg_interval), abs(chro_interval)) not in FORBIDDEN_INTERVAL_COMBINATIONS:
            if note1.get_accidental == ScaleOption.NATURAL or note2.get_accidental == ScaleOption.NATURAL or chro_interval == 2:
                return True
        return False 

    def _valid_outline(self, note1: Note, note2: Note) -> bool:
        chro_interval = note1.get_chromatic_interval(note2)
        sdg_interval = note1.get_scale_degree_interval(note2)
        if chro_interval in CONSONANT_MELODIC_INTERVALS_CHROMATIC and (abs(sdg_interval), abs(chro_interval)) not in FORBIDDEN_INTERVAL_COMBINATIONS:
            return True
        return False 

    def _valid_range(self, note1: Note, note2: Note) -> bool:
        if self._valid_outline(note1, note2): return True 
        if note1.get_scale_degree_interval(note2) == 7: return True 
        return False 

    def _get_default_note_from_interval(self, note: Note, interval: int) -> Note:
        candidates = self._get_notes_from_interval(note, interval)
        if len(candidates) == 0: return None 
        note = candidates[0]
        self._mr.make_default_scale_option(note)
        return note
    
    #returns valid notes, if any, at the specified interval.  "3" returns a third above.  "-5" returns a fifth below
    def _get_notes_from_interval(self, note: Note, interval: int) -> list[Note]: 
        sdg = note.get_scale_degree()
        octv = note.get_octave()
        adjustment_value = -1 if interval > 0 else 1
        new_sdg, new_octv = sdg + interval + adjustment_value, octv
        if new_sdg < 1:
            new_octv -= 1
            new_sdg += 7
        elif new_sdg > 7:
            new_octv += 1
            new_sdg -= 7
        new_note = Note(new_sdg, new_octv, 8)
        valid_notes = [new_note]
        if (self._mode == ModeOption.DORIAN or self._mode == ModeOption.LYDIAN) and new_sdg == 7:
            valid_notes.append(Note(new_sdg, new_octv, 8, accidental = ScaleOption.FLAT))
        def valid_interval(next_note: Note) -> bool:
            chro_interval = next_note.get_chromatic_with_octave() - note.get_chromatic_with_octave()
            return chro_interval in CONSONANT_MELODIC_INTERVALS_CHROMATIC
        return list(filter(valid_interval, valid_notes))
