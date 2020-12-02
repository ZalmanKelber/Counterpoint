from random import random, shuffle

from notation_system import ModeOption, ScaleOption, Note, ModeResolver 
import math

#intervals it is permissible to move directly to
VALID_MELODIC_INTERVALS_CHROMATIC = { -12, -7, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 7, 8, 12 }
#intervals it is permissible to outline
CONSONANT_MELODIC_INTERVALS_CHROMATIC = { -12, -9, -8 -7, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7, 8, 9, 12 }
#intervals it is permissible to move directly to, as scale degrees
VALID_MELODIC_INTERVALS_SCALE_DEGREES = { -8, -5, -4, -3, -2, 2, 3, 4, 5, 6, 8 }

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

class CantusFirmus:
    def __init__(self, length: int, mode: ModeOption, octave: int = 4):
        self._notes = [None for i in range(length)]
        self._mode = mode
    
    def insert_note(self, note: Note, index: int) -> None:
        self._notes[index] = note 

    def get_note(self, index: int) -> Note:
        return self._notes[index]


class GenerateCantusFirmus:
    #for our constructor function, if no default length or mode is given, generate a random one
    def __init__(self, length: int = None, mode: ModeOption = None, octave: int = 4):
        self._mode = mode or MODES_BY_INDEX[math.floor(random() * 6)]
        self._length = length or 8 + math.floor(random() * 5) #todo: replace with normal distribution
        self._octave = octave
        self._mr = ModeResolver(self._mode)
        self._cf = CantusFirmus(self._length, self._mr, self._octave)
        
    def generate_cf(self):
        self._initialize_cf()
        #self._backtrack_cf()

    def _initialize_cf(self):
        #"final" is equal to the mode's starting scale degree.  All notes in the cantus firmus will be whole notes
        final = Note(self._mode.value["starting"], self._octave, 8) 
        #add the "final" to the first and last pitches 
        for index in [0, self._length - 1]:
            self._cf.insert_note(final, index)
        #find all notes eligible to be highest note
        possible_highest_notes = []
        for interval in VALID_MELODIC_INTERVALS_SCALE_DEGREES:
            if interval > 1:
                possible_highest_notes += self._get_notes_from_interval(final, interval)
        #filter out two particular cases (highest note can't be B natural in Dorian and can't be F in Phrygian)
        def remove_edge_cases(tpl: tuple) -> bool:
            note = tpl[1]
            if self._mode == ModeOption.PHRYGIAN and note.get_scale_degree() == 4: 
                return False
            if self._mode == ModeOption.DORIAN and note.get_scale_degree() == 7 and note.get_accidental() == ScaleOption.NATURAL:
                return False
            return True
        possible_highest_notes = list(filter(remove_edge_cases, possible_highest_notes))
        print("mode = ", self._mode.value["name"])
        # for n in possible_highest_notes:
        #     print(n[0], n[1])
        final_to_highest_interval, highest_note = possible_highest_notes[math.floor(random() * len(possible_highest_notes)) ]
        print("highest note = ", highest_note)
        #based on the highest we've chosen, find possible lowest notes
        possible_lowest_notes = []
        for interval in GET_POSSIBLE_INTERVALS_TO_LOWEST[final_to_highest_interval]:
            possible_lowest_notes += self._get_notes_from_interval(final, interval)
        #remove candidates that form tritones with highest note (sevenths are permissible)
        def check_range_interval(tpl: tuple) -> bool:
            note = tpl[1]
            if highest_note.get_chromatic_with_octave() - note.get_chromatic_with_octave() == 6:
                return False 
            return True
        possible_lowest_notes = list(filter(check_range_interval, possible_lowest_notes))
        final_to_lowest_interval, lowest_note = possible_lowest_notes[math.floor(random() * len(possible_lowest_notes))]
        print("lowest note = ", lowest_note)
        #note that we exclude the highest interval when calculating possible valid notes since highest note can only appear once
        valid_intervals_from_final = list(range(1, final_to_highest_interval)) 
        if final_to_lowest_interval < 0: valid_intervals_from_final += list(range(final_to_lowest_interval, -1)) 
        valid_pitches = []
        for interval in valid_intervals_from_final:
            valid_pitches += self._get_notes_from_interval(final, interval)
        self.valid_pitches = list(map(lambda tpl: tpl[1], valid_pitches))

        #see whether it's possible to end Cantus Firmus from below (either by step or from the "dominant")
        final_to_dom_interval = -4 if self._mode.value["most_common"] == 5 else -5
        can_end_from_dominant = final_to_dom_interval >= final_to_lowest_interval
        can_end_from_step_below = final_to_lowest_interval <= -2

        #set penultimate note as a step above the final as default
        final_to_penult_interval, penult_note = self._get_notes_from_interval(final, 2)[0]
        if random() > .9: #note that in no cases do we need to worry about b-flat vs b-natural here
            if can_end_from_dominant:
                final_to_penult_interval, penult_note = self._get_notes_from_interval(final, final_to_dom_interval)[0]
            elif can_end_from_step_below:
                final_to_penult_interval, penult_note = self._get_notes_from_interval(final, -2)[0]
        
        #insert the penultimate note into the Cantus Firmus
        self._cf.insert_note(penult_note, self._length - 2)

        #initialize remaining indices
        self._remaining_indices = [i for i in range(1, self._length - 2)]

        #if we haven't already added the highest note, add it:
        if final_to_penult_interval != final_to_highest_interval:
            self._add_highest(highest_note)
        
        #if we haven't already added the lowest note, add it:
        if final_to_lowest_interval != final_to_penult_interval and final_to_lowest_interval != 1:
            self._add_lowest(lowest_note)

    #inserts the highest note into a random unoccupied place in the Cantus Firmus that is not the center
    def _add_highest(self, note: Note) -> None:
        def remove_center_position(index: int) -> bool:
            if self._length % 2 == 1 and index == math.floor(self._length / 2):
                return False 
            return True
        possible_indices = list(filter(remove_center_position, [num for num in self._remaining_indices]))
        shuffle(possible_indices)
        print("shuffled indices:", possible_indices)
        for index in possible_indices:
            prev_note = self._cf.get_note(index - 1)
            if prev_note is None or (prev_note.get_scale_degree_interval(note) in VALID_MELODIC_INTERVALS_SCALE_DEGREES and prev_note.get_chromatic_interval(note) in VALID_MELODIC_INTERVALS_CHROMATIC):
                next_note = self._cf.get_note(index + 1)
                #if the next note is not empty we need to make sure that leaps are handled correctly at the end of the piece
                if next_note is None or (note.get_scale_degree_interval(next_note) in VALID_MELODIC_INTERVALS_SCALE_DEGREES and note.get_chromatic_interval(next_note) in VALID_MELODIC_INTERVALS_CHROMATIC):
                    #if there is a leap down to the penultimate note, we need to make sure that the highest note is only a step higher than the final
                    if next_note is None or note.get_scale_degree_interval(next_note) == -2 or note.get_scale_degree_interval(self._cf.get_note(index + 2)):
                        self._cf.insert_note(note, index)
                        self._remaining_indices.remove(index)
                        print("removed index", index)
                        break
            print("failed to insert highest note at index", index)
        for n in self._cf._notes:
            print(n)


    def _add_lowest(self, note: Note) -> None:
        pass




        

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
        if self._mode == ModeOption.DORIAN and new_sdg == 7:
            valid_notes.append(Note(new_sdg, new_octv, 8, accidental = ScaleOption.FLAT))
        def valid_interval(next_note: Note) -> bool:
            chro_interval = next_note.get_chromatic_with_octave() - note.get_chromatic_with_octave()
            return chro_interval in CONSONANT_MELODIC_INTERVALS_CHROMATIC
        return list(map(lambda n: (interval, n), list(filter(valid_interval, valid_notes))))

gcf1 = GenerateCantusFirmus(8, ModeOption.DORIAN)
gcf2 = GenerateCantusFirmus(11, ModeOption.PHRYGIAN)
gcf3 = GenerateCantusFirmus(8, ModeOption.IONIAN, octave = 3)
for gcf in [gcf1, gcf2, gcf3]:
    gcf.generate_cf()
