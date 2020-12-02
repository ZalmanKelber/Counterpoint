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

#this is the average proportion of intervals that are steps in Jeppesen's Cantus Firmus examples
AVERAGE_STEPS_PERCENTAGE = .712

class CantusFirmus:
    def __init__(self, length: int, mode: ModeOption, octave: int = 4):
        self._notes = [None for i in range(length)]
        self._mode = mode
    
    def insert_note(self, note: Note, index: int) -> None:
        self._notes[index] = note 

    def get_note(self, index: int) -> Note:
        return self._notes[index]

    def print_cf(self) -> None:
        for note in self._notes:
            print(note)


class GenerateCantusFirmus:
    #for our constructor function, if no default length or mode is given, generate a random one
    def __init__(self, length: int = None, mode: ModeOption = None, octave: int = 4):
        self._mode = mode or MODES_BY_INDEX[math.floor(random() * 6)]
        self._length = length or 8 + math.floor(random() * 5) #todo: replace with normal distribution
        self._octave = octave
        self._mr = ModeResolver(self._mode)
        self._cf = CantusFirmus(self._length, self._mr, self._octave)
        
    def generate_cf(self) -> CantusFirmus:
        print("MODE = ", self._mode.value["name"])
        run_count = 1
        self._solutions = []
        self._initialize_cf()
        self._backtrack_cf()
        while len(self._solutions) == 0 and run_count < 100:
            run_count += 1
            self._initialize_cf()
            self._backtrack_cf()
        print("number of solutions found:", len(self._solutions))
        print("attempts:", run_count)
        self._solutions = sorted(self._solutions, key = self._steps_are_proportional)
        for i, note in enumerate(self._solutions[0]):
            self._cf.insert_note(note, i)
        return self._cf
        
    def _steps_are_proportional(self, solution: list[Note]) -> int:
        steps = 0
        for i in range(1, len(solution)):
            if abs(solution[i - 1].get_scale_degree_interval(solution[i])) == 2:
                steps += 1
        proportion = steps / (len(solution) - 1)
        return abs(proportion - AVERAGE_STEPS_PERCENTAGE)

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
        
        final_to_highest_interval, highest_note = possible_highest_notes[math.floor(random() * len(possible_highest_notes)) ]
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
        #note that we exclude the highest interval when calculating possible valid notes since highest note can only appear once
        valid_intervals_from_final = list(range(1, final_to_highest_interval)) 
        if final_to_lowest_interval < 0: valid_intervals_from_final += list(range(final_to_lowest_interval, -1)) 
        valid_pitches = []
        for interval in valid_intervals_from_final:
            valid_pitches += self._get_notes_from_interval(final, interval)
        self._valid_pitches = list(map(lambda tpl: tpl[1], valid_pitches))

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
        remaining_indices = [i for i in range(1, self._length - 2)]
        remaining_indices.reverse()
        self._remaining_indices = remaining_indices

        #if we haven't already added the highest note, add it:
        if final_to_penult_interval != final_to_highest_interval:
            self._add_highest(highest_note)
        
        #if we haven't already added the lowest note, add it:
        if final_to_lowest_interval != final_to_penult_interval and final_to_lowest_interval != 1:
            self._add_lowest(lowest_note)

    def _valid_melodic_interval(self, first_note: Note, second_note: Note) -> bool:
        scale_interval = first_note.get_scale_degree_interval(second_note)
        chro_interval = first_note.get_chromatic_interval(second_note)
        if scale_interval not in VALID_MELODIC_INTERVALS_SCALE_DEGREES: return False 
        if chro_interval not in VALID_MELODIC_INTERVALS_CHROMATIC: return False
        return True

    #inserts the highest note into a random unoccupied place in the Cantus Firmus that is not the center
    def _add_highest(self, note: Note) -> None:
        def remove_center_position(index: int) -> bool:
            if self._length % 2 == 1 and index == math.floor(self._length / 2):
                return False 
            return True
        possible_indices = list(filter(remove_center_position, [num for num in self._remaining_indices]))
        shuffle(possible_indices)
        correct_index = None
        for index in possible_indices:
            correct_index = index
            prev_note = self._cf.get_note(index - 1)
            next_note = self._cf.get_note(index + 1)
            if prev_note is None and next_note is None:
                break
            if prev_note is not None and self._valid_melodic_interval(prev_note, note):
                break 
            if prev_note is not None and not self._valid_melodic_interval(prev_note, note):
                continue 
            if next_note is not None and not self._valid_melodic_interval(note, next_note):
                continue
            if next_note is not None and self._valid_melodic_interval(note, next_note):
                #we need to check if the final three notes are handled correctly
                if note.get_scale_degree_interval(next_note) == -2:
                    break 
                #if we leap down, this can't be followed by a downward step
                final = self._cf.get_note(index + 2)
                if next_note.get_scale_degree_interval(final) == -2:
                    continue
                #otherwise we're legal
                break 
        self._cf.insert_note(note, correct_index)
        self._remaining_indices.remove(correct_index)


    def _add_lowest(self, note: Note) -> None:
        possible_indices = [num for num in self._remaining_indices]
        shuffle(possible_indices)
        correct_index = None
        for index in possible_indices:
            #for each index, there are several scenarios:
            #index is preceded by a note (either the highest or the lowest)
            #index is followed by a note (either the highest followed by a blank, the penultimate, or the highest followed by penultimate)
            correct_index = index
            prev_note = self._cf.get_note(index - 1)
            next_note = self._cf.get_note(index + 1)
            note_after_next = self._cf.get_note(index + 2)
            if prev_note is None and next_note is None:
                break
            if prev_note is not None and not self._valid_melodic_interval(prev_note, note):
                continue 
            if next_note is not None and not self._valid_melodic_interval(note, next_note):
                continue
            if next_note is None or note_after_next is None:
                break
            if next_note is not None and note_after_next is not None: #we are in the third to last or fourth to last position
                if index == self._length - 3:
                    #if index is the antipenultimate position, there are no scenarios in which
                    #lowest note -> penultimate -> final have an improper sequence of intervals
                    break 
                #otherwise we need to make sure that a leap to the highest note is handled properly
                final = self._cf.get_note(index + 3)
                lowest_to_highest = note.get_scale_degree_interval(next_note)
                lowest_to_penult = note.get_scale_degree_interval(note_after_next)
                lowest_to_final = note.get_scale_degree_interval(final)
                if lowest_to_highest > 3 and lowest_to_penult != lowest_to_highest - 1 and lowest_to_final != lowest_to_highest - 1:
                    continue
                else:
                    break
        self._cf.insert_note(note, correct_index)
        self._remaining_indices.remove(correct_index)

    def _backtrack_cf(self) -> None:
        if len(self._remaining_indices) == 0:
            solution = []
            for i in range(self._length):
                solution.append(self._cf.get_note(i))
            if self._ascending_intervals_are_handled(solution) and self._no_intervalic_sequences(solution):
                self._solutions.append(solution) 
            return
        index = self._remaining_indices.pop()
        prev_note = self._cf.get_note(index - 1) #will never be None
        next_note = self._cf.get_note(index + 1) #may be None
        def intervals_are_valid(possible_note: Note) -> bool:
            if not self._valid_melodic_interval(prev_note, possible_note): return False 
            if next_note is not None and not self._valid_melodic_interval(possible_note, next_note): return False 
            return True
        possible_pitches = list(filter(intervals_are_valid, self._valid_pitches))
        possible_pitches = sorted(possible_pitches, key = lambda n: abs(prev_note.get_chromatic_interval(n)))
        for possible_note in possible_pitches:
            self._cf.insert_note(possible_note, index)
            if self._current_chain_is_legal():
                self._backtrack_cf()
            self._cf.insert_note(None, index)

        self._remaining_indices.append(index)

    def _current_chain_is_legal(self) -> bool:
        #check for the following:
        #1. no dissonant intervals outlined in "segments" (don't check last segment)
        #2. no dissonant intervals outlined in "leap chains"
        #3. ascending minor sixths followed by descending minor seconds
        #4. in each segment, intervals must become progressively smaller (3 -> 2 or -2 -> -3, etc)
        #5. check if ascending leaps greater than a fourth are followed by descending second (to high degree of proability)
        #6. make sure there are no sequences of two notes that are immediately repeated
        #7. check for cross relations

        #keep track of whether we have a b-flat or b-natural
        has_b_natural = False
        has_b_flat = False

        #start by getting current chain of notes and keeping track of b's and b-flats:
        current_chain = []
        for i in range(self._length):
            note = self._cf.get_note(i)
            if note is None: break
            current_chain.append(note)
            if note.get_scale_degree() == 7:
                if note.get_accidental() == ScaleOption.FLAT: 
                    has_b_flat = True 
                else: 
                    has_b_natural = True 
        if has_b_natural and has_b_flat:
            return False 
        #next, get the segments (consecutive notes that move in the same direction)
        #and the leap chains (consecutive notes separated by leaps)
        segments = [[current_chain[0]]]
        leap_chains = [[current_chain[0]]]
        prev_interval = None 
        for i in range(1, len(current_chain)):
            note = current_chain[i]
            prev_note = current_chain[i - 1]
            current_interval = prev_note.get_scale_degree_interval(note)
            if prev_interval is None or (prev_interval > 0 and current_interval > 0) or (prev_interval < 0 and current_interval < 0):
                segments[-1].append(note)
            else:
                segments.append([prev_note, note])
            if abs(current_interval) <= 2:
                leap_chains.append([note])
            else:
                leap_chains[-1].append(note)
            prev_interval = current_interval
        #we only need to examine segments and chains of length 3 or greater
        leap_chains = list(filter(lambda chain: len(chain) >= 3, leap_chains))
        segments = list(filter(lambda seg: len(seg) >= 3, segments))

        #check segments
        for i, seg in enumerate(segments):
            #check for dissonant intervals except in last segment unless we're checking the completed Cantus Firmus
            if i < len(segments) - 1 or len(current_chain) == self._length:
                if self._segment_outlines_illegal_interval(seg):
                    return False 
            if self._segment_has_illegal_interval_ordering(seg):
                return False

        #check leap chains
        for chain in leap_chains:
            if self._leap_chain_is_illegal(chain):
                return False 

        #check for ascending intervals 
        for i in range(1, len(current_chain) - 1):
            first_interval = current_chain[i - 1].get_scale_degree_interval(current_chain[i])
            if first_interval == 6:
                second_interval_chromatic = current_chain[i].get_chromatic_interval(current_chain[i + 1])
                if second_interval_chromatic != -1:
                    return False 
            if first_interval > 3:
                second_interval_sdg = current_chain[i].get_scale_degree_interval(current_chain[i + 1])
                if second_interval_sdg != -2 and random() > .5:
                    return False 

        #check for no sequences
        for i in range(3, len(current_chain)):
            if current_chain[i - 3].get_chromatic_interval(current_chain[i - 1]) == 0 and current_chain[i - 2].get_chromatic_interval(current_chain[i]) == 0:
                return False 
        
        return True

    def _leap_chain_is_illegal(self, chain: list[Note]) -> bool:
        for i in range(len(chain) - 2):
            for j in range(i + 2, len(chain)):
                chro_interval = chain[i].get_chromatic_interval(chain[j])
                if chro_interval not in CONSONANT_MELODIC_INTERVALS_CHROMATIC:
                    return True 
        return False

    def _segment_outlines_illegal_interval(self, seg: list[Note]) -> bool:
        chro_interval = seg[0].get_chromatic_interval(seg[-1])
        return chro_interval not in CONSONANT_MELODIC_INTERVALS_CHROMATIC

    def _segment_has_illegal_interval_ordering(self, seg: list[Note]) -> bool:
        prev_interval = seg[0].get_scale_degree_interval(seg[1])
        for i in range(1, len(seg)):
            current_interval = seg[i - 1].get_scale_degree_interval(seg[i])
            if current_interval > prev_interval:
                return True
            prev_interval = current_interval
        return False

    def _ascending_intervals_are_handled(self, solution: list[Note]) -> bool:
        for i in range(1, len(solution) - 1):
            interval = solution[i - 1].get_scale_degree_interval(solution[i])
            if interval > 2:
                filled_in = False 
                for j in range(i + 1, len(solution)):
                    if solution[i].get_scale_degree_interval(solution[j]) == -2:
                        filled_in = True
                        break
                if not filled_in: return False 
        return True

    
    def _no_intervalic_sequences(self, solution: list[Note]) -> bool:
        #check if an intervalic sequence of four or more notes repeats
        intervals = []
        for i in range(1, len(solution)):
            intervals.append(solution[i - 1].get_scale_degree_interval(solution[i]))
        for i in range(len(solution) - 6):
            seq = intervals[i: i + 3]
            for j in range(i + 3, len(solution) - 4):
                possible_match = intervals[j: j + 3]
                if seq == possible_match:
                    return False 

        #check to remove pattern leap down -> step up -> step down -> leap up
        for i in range(len(solution) - 4):
            if intervals[i] < -2 and intervals[i + 1] == 2 and intervals[i + 2] == -2 and intervals[i + 3] > 2:
                if random() > .8:
                    return False
        #check if three exact notes repeat
        for i in range(len(solution) - 5):
            for j in range(i + 3, len(solution) - 2):
                if solution[i].get_chromatic_interval(solution[j]) == 0 and solution[i + 1].get_chromatic_interval(solution[j + 1]) == 0 and solution[i + 2].get_chromatic_interval(solution[j + 2]) == 0:
                    return False 
        return True
        


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
