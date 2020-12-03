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
CONSONANT_HARMONIC_INTERVALS_CHROMATIC = { 0, 3, 4, 7, 8, 9, 12 }
#permissible harmonic scale degree intervals (unison not included since they aren't allowed anywhere except ends)
CONSONANT_HARMONIC_INTERVALS_SCALE_DEGREES = { -10, -8, -6, -5, -3, 3, 5, 6, 8, 10 }
#illegal combinations of sdg intervals and chromatic intervals that result in augmented or diminished intervals 
#respectively: cross relations, augmented seconds, diminished thirds, diminished fourths, augmented fifths and augmented sixths
FORBIDDEN_INTERVAL_COMBINATIONS = { (1, 1), (1, 11), (2, 3), (3, 2), (4, 4), (5, 8), (6, 10) }

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

#acceptable max number of a repeated note, based on the length of the counterpoint
MAX_ACCEPTABLE_REPITITIONS_BASED_ON_LENGTH = { 8: 3, 9: 3, 10: 3, 11: 4, 12: 4 }

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

    def print_counterpoint(self):
        print("  CANTUS FIRMUS:       COUNTERPOINT:")
        for i in range(self._length):
            print("  " + str(self._cf.get_note(i)) + "  " + str(self._counterpoint[i]))


    def generate_2p1s(self):
        print("MODE = ", self._mode.value["name"])
        self._solutions = []
        def attempt():
            initialized = self._initialize()
            while not initialized:
                initialized = self._initialize()
            self._backtrack()
        attempt()
        attempts = 1
        while len(self._solutions) < 30 and attempts < 1000:
            attempts += 1
            attempt()
        print("number of attempts:", attempts)
        print("number of solutions:", len(self._solutions))
        if len(self._solutions) > 0:
            self._solutions.sort(key = lambda sol: self._score_solution(sol))
            optimal = self._solutions[0]
            worst = self._solutions[-1]
            self._counterpoint = optimal
            print("optimal solution:")
            self.print_counterpoint()
            self._counterpoint = worst
            print("worst solution:")
            self.print_counterpoint()


    #create the list we will backtrack through, find first, last, highest and lowest notes
    def _initialize(self) -> bool:
        #initializae the list we will use to store our counterpoint
        self._counterpoint = [None] * self._length
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

        #adjust penult_note 
        if end_to_penult_interval == -2 and ending_interval != 5: #that is, if we're approaching the mode final from below
            if self._mode in [ModeOption.DORIAN, ModeOption.MIXOLYDIAN, ModeOption.AEOLIAN] and random() > .5:
                penult_note.set_accidental(ScaleOption.SHARP)

        #find lowest note so far
        lowest_so_far = first_note if (starting_interval < ending_interval and end_to_penult_interval > -5) else last_note if end_to_penult_interval > 0 else penult_note
        #get possible lowest notes 
        lowest_note_candidates = [lowest_so_far]
        for i in range(1, 8 - range_so_far):
            candidate = self._get_default_note_from_interval(lowest_so_far, (i + 1) * -1)
            if self._valid_outline(first_note, candidate) and self._valid_outline(last_note, candidate):
                if self._orientation == Orientation.BELOW or cf_highest.get_scale_degree_interval(candidate) >= -3:
                    lowest_note_candidates.append(candidate)
        lowest_note = lowest_note_candidates[math.floor(random() * len(lowest_note_candidates))]
        range_so_far += lowest_note.get_scale_degree_interval(lowest_so_far) - 1
        #find highest note so far
        highest_so_far = first_note if starting_interval > ending_interval else penult_note if end_to_penult_interval > 0 else last_note
        #get possible highest notes
        highest_note_candidates = [highest_so_far] if (starting_interval > ending_interval or end_to_penult_interval > 0) and range_so_far >= 6 else []
        for i in range(max(6 - range_so_far, 0), 8 - range_so_far):
            candidate = self._get_default_note_from_interval(highest_so_far, i + 1)
            if candidate.get_accidental() != ScaleOption.SHARP and self._valid_range(lowest_note, candidate) and self._valid_outline(first_note, candidate) and self._valid_outline(last_note, candidate):
                if self._orientation == Orientation.ABOVE or cf_lowest.get_scale_degree_interval(candidate) <= -3:
                    if not (self._mode == ModeOption.DORIAN and candidate.get_accidental() == ScaleOption.NATURAL and candidate.get_scale_degree() == 7):
                        highest_note_candidates.append(candidate)
        highest_note = highest_note_candidates[math.floor(random() * len(highest_note_candidates))]

        #initialize list of remaining indices 
        remaining_indices = list(range(1, self._length - 2))
        remaining_indices.reverse()
        self._remaining_indices = remaining_indices 

        #find all valid notes (include lowest, but don't include highest)
        valid_notes = [lowest_note]
        #define the filter function that eliminates cross relations 
        def remove_cross_relations(candidate: Note) -> bool:
            for fixed in [first_note, penult_note, last_note, highest_note, lowest_note]:
                if fixed.get_scale_degree_interval(candidate) == 1 and fixed.get_chromatic_interval(candidate) != 0:
                    return False 
            return True 
        for i in range(2, lowest_note.get_scale_degree_interval(highest_note)):
            valid_notes += self._get_notes_from_interval(lowest_note, i)
        self._valid_notes = list(filter(remove_cross_relations, valid_notes))

        #add three notes to counterpoint
        self._counterpoint[0] = first_note
        self._counterpoint[-2] = penult_note
        self._counterpoint[-1] = last_note

        #add highest and lowest notes if they're not already in 
        if highest_so_far.get_chromatic_interval(highest_note) != 0:
            added_high_note = self._add_highest(highest_note)
            if not added_high_note:
                return False 
        if lowest_note.get_chromatic_interval(lowest_so_far) != 0:
            added_low_note = self._add_lowest(lowest_note)
            if not added_low_note:
                return False
        return True 
        

    def _add_highest(self, note: Note) -> bool:
        remaining_indices = self._remaining_indices[:]
        if self._length % 2 == 1:
            remaining_indices.remove(math.floor(self._length / 2))
        shuffle(remaining_indices)
        index = None
        while len(remaining_indices) > 0:
            index = remaining_indices.pop()
            #we will need to see if the position works 1. harmonically, 2. melooically, 3. does not create parallels
            prev_note = self._counterpoint[index - 1]
            next_note = self._counterpoint[index + 1]
            cf_note = self._cf.get_note(index)
            #check if placement is melodically valid
            if prev_note is not None and not self._valid_adjacent(prev_note, note):
                continue 
            if next_note is not None and not self._valid_adjacent(note, next_note):
                continue
            #check if placement is harmonically valid
            if not self._valid_harmonically(note, cf_note):
                continue
            #check if placement creates parallel or hidden fifths or octaves
            if not self._doesnt_create_hiddens_or_parallels(note, index):
                continue 
            #check that placement doesn't create an illegal segment
            if next_note is not None:
                note_after_next = self._counterpoint[index + 2]
                if next_note.get_scale_degree_interval(note_after_next) < 0 and not self._segment_has_legal_shape([note, next_note, note_after_next]):
                    continue
            break 
        if len(remaining_indices) == 0:
            return False 
        self._remaining_indices.remove(index)
        self._counterpoint[index] = note
        return True 

    def _add_lowest(self, note: Note) -> bool:
        remaining_indices = self._remaining_indices[:]
        shuffle(remaining_indices)
        index = None
        while len(remaining_indices) > 0:
            index = remaining_indices.pop()
            #we will need to see if the position works 1. harmonically, 2. melooically, 3. does not create parallels
            prev_note = self._counterpoint[index - 1]
            next_note = self._counterpoint[index + 1]
            cf_note = self._cf.get_note(index)
            #check if placement is melodically valid
            if prev_note is not None and not self._valid_adjacent(prev_note, note):
                continue 
            if next_note is not None and not self._valid_adjacent(note, next_note):
                continue
            #check if placement is harmonically valid
            if not self._valid_harmonically(note, cf_note):
                continue
            #check if placement creates parallel or hidden fifths or octaves
            if not self._doesnt_create_hiddens_or_parallels(note, index):
                continue 
            #get total span of consecutive notes
            start_index, end_index = index, index + 1
            while start_index != 0 and self._counterpoint[start_index - 1] is not None:
                start_index -= 1 
            while end_index < self._length and self._counterpoint[end_index] is not None:
                end_index += 1
            #will have maximum length of 4
            span = self._counterpoint[start_index: end_index]
            span[index - start_index] = note
            if len(span) < 3:
                break
            leap_chain = [span[0], span[1]] if abs(span[0].get_scale_degree_interval(span[1])) > 2 else [span[1]]
            for i in range(2, len(span)):
                if abs(span[i - 1].get_scale_degree_interval(span[i])) <= 2: break 
                leap_chain.append(span[i])
            if not self._leap_chain_is_legal(leap_chain):
                continue 
            first_interval, second_interval = span[0].get_scale_degree_interval(span[1]), span[1].get_scale_degree_interval(span[2])
            segment = [span[0], span[1]] if (first_interval > 0 and second_interval > 0) or (first_interval < 0 and second_interval < 0) else [span[1]]
            for i in range(2, len(span)):
                ith_interval = span[i - 1].get_scale_degree_interval(span[i]) 
                if not (second_interval > 0 and ith_interval > 0) and not (second_interval < 0 and ith_interval < 0):
                    break 
                segment.append(span[i])
            if not self._segment_has_legal_shape(segment):
                continue 
            break 
        if len(remaining_indices) == 0:
            return False 
        self._remaining_indices.remove(index)
        self._counterpoint[index] = note
        return True 

    def _backtrack(self) -> None:
        if len(self._remaining_indices) == 0:
            if self._passes_final_checks():
                self._solutions.append(self._counterpoint[:])
            return 
        index = self._remaining_indices.pop()
        against = self._cf.get_note(index)
        prev_note = self._counterpoint[index - 1]
        next_note = self._counterpoint[index + 1]
        #filter out notes that are 1. not harmonically valid, 2. not melodically valid, 3. create parallels and 4. create a cross relation with an already added note 
        possible_notes = self._valid_notes[:]
        possible_notes = list(filter(lambda n: self._valid_harmonically(n, against), possible_notes))
        possible_notes = list(filter(lambda n: self._valid_adjacent(prev_note, n), possible_notes))
        if next_note is not None:
            possible_notes = list(filter(lambda n: self._valid_adjacent(n, next_note), possible_notes))
        possible_notes = list(filter(lambda n: self._doesnt_create_hiddens_or_parallels(n, index), possible_notes))
        possible_notes = list(filter(lambda n: self._no_large_parallel_leaps(n, index), possible_notes))
        possible_notes = list(filter(lambda n: self._no_cross_relations_with_previously_added(n), possible_notes))

        #we will find all solutions so sorting possible_notes isn't necessary
        for candidate in possible_notes:
            self._counterpoint[index] = candidate 
            if self._current_chain_is_legal():
                self._backtrack()
        self._counterpoint[index] = None 
        self._remaining_indices.append(index)

    def _current_chain_is_legal(self) -> bool:
        #check for the following:
        #1. no dissonant intervals outlined in "segments" (don't check last segment)
        #2. no dissonant intervals outlined in "leap chains"
        #3. ascending minor sixths followed by descending minor seconds
        #4. in each segment, intervals must become progressively smaller (3 -> 2 or -2 -> -3, etc)
        #5. check if ascending leaps greater than a fourth are followed by descending second (to high degree of proability)
        #6. make sure there are no sequences of two notes that are immediately repeated

        #start by getting current chain of notes 
        current_chain = []
        for i in range(self._length):
            if self._counterpoint[i] is None: break
            current_chain.append(self._counterpoint[i])
            
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

        #check segments
        for i, seg in enumerate(segments):
            #check for dissonant intervals except in last segment unless we're checking the completed Cantus Firmus
            if i < len(segments) - 1 or len(current_chain) == self._length:
                if not self._segment_outlines_legal_interval(seg):
                    return False 
            if not self._segment_has_legal_shape(seg):
                return False

        #check leap chains
        for chain in leap_chains:
            if not self._leap_chain_is_legal(chain):
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
        
    def _passes_final_checks(self) -> bool:
        return self._no_intervalic_sequences() and self._ascending_intervals_handled() and self._no_extended_parallel_motion()

    def _no_intervalic_sequences(self) -> bool:
        #check if an intervalic sequence of four or more notes repeats
        intervals = []
        for i in range(1, self._length):
            intervals.append(self._counterpoint[i - 1].get_scale_degree_interval(self._counterpoint[i]))
        for i in range(self._length - 6):
            seq = intervals[i: i + 3]
            for j in range(i + 3, self._length - 4):
                possible_match = intervals[j: j + 3]
                if seq == possible_match:
                    return False 

        #check to remove pattern leap down -> step up -> step down -> leap up
        for i in range(self._length - 4):
            if intervals[i] < -2 and intervals[i + 1] == 2 and intervals[i + 2] == -2 and intervals[i + 3] > 2:
                if random() < .8:
                    return False
        #check if three exact notes repeat
        for i in range(self._length - 5):
            for j in range(i + 3, self._length - 2):
                if self._counterpoint[i].get_chromatic_interval(self._counterpoint[j]) == 0 and self._counterpoint[i + 1].get_chromatic_interval(self._counterpoint[j + 1]) == 0 and self._counterpoint[i + 2].get_chromatic_interval(self._counterpoint[j + 2]) == 0:
                    return False 
        return True

    def _ascending_intervals_handled(self) -> bool:
        for i in range(1, self._length - 1):
            interval = self._counterpoint[i - 1].get_scale_degree_interval(self._counterpoint[i])
            if interval > 2:
                filled_in = False 
                for j in range(i + 1, self._length):
                    if self._counterpoint[i].get_scale_degree_interval(self._counterpoint[j]) == -2:
                        filled_in = True
                        break
                if not filled_in: return False 
        return True

    def _no_extended_parallel_motion(self) -> bool:
        prev_harmonic_interval = None
        count = 0
        for i in range(self._length):
            cur_harmonic_interval = self._counterpoint[i].get_scale_degree_interval(self._cf.get_note(i))
            if cur_harmonic_interval == prev_harmonic_interval:
                count += 1
            else: 
                count = 0
            if count == 4:
                print("too much parallel motion")
                return False 
        return True 

    def _valid_adjacent(self, note1: Note, note2: Note) -> bool:
        chro_interval = note1.get_chromatic_interval(note2)
        sdg_interval = note1.get_scale_degree_interval(note2)
        if chro_interval in VALID_MELODIC_INTERVALS_CHROMATIC and (abs(sdg_interval), abs(chro_interval)) not in FORBIDDEN_INTERVAL_COMBINATIONS:
            if note1.get_accidental() == ScaleOption.NATURAL or note2.get_accidental() == ScaleOption.NATURAL or abs(chro_interval) == 2:
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
    
    def _valid_harmonically(self, note1: Note, note2: Note) -> bool:
        chro_interval = note1.get_chromatic_interval(note2)
        if chro_interval == 0: return False
        sdg_interval = note1.get_scale_degree_interval(note2)
        if sdg_interval in CONSONANT_HARMONIC_INTERVALS_SCALE_DEGREES and chro_interval % 12 in CONSONANT_MELODIC_INTERVALS_CHROMATIC:
            combo = (abs(sdg_interval if sdg_interval <= 8 else sdg_interval - 7), abs(chro_interval) % 12)
            if combo not in FORBIDDEN_INTERVAL_COMBINATIONS:
                return True 
        return False 

    def _no_large_parallel_leaps(self, note: Note, index: int) -> bool:
        prev_note = self._counterpoint[index - 1]
        next_note = self._counterpoint[index + 1]
        cf_note = self._cf.get_note(index)
        cf_prev_note = self._cf.get_note(index - 1)
        cf_next_note = self._cf.get_note(index + 1)
        if prev_note is not None:
            prev_interval = prev_note.get_scale_degree_interval(note)
            cf_prev_interval = cf_prev_note.get_scale_degree_interval(cf_note)
            if (prev_interval > 2 and cf_prev_interval > 2) or (prev_interval < -2 and cf_prev_interval < -2):
                if abs(prev_interval) > 4 or abs(cf_prev_interval) > 4:
                    return False 
        if next_note is not None:
            next_interval = note.get_scale_degree_interval(next_note)
            cf_next_interval = cf_note.get_scale_degree_interval(cf_next_note)
            if (next_interval > 2 and cf_next_interval > 2) or (next_interval < -2 and cf_next_interval < -2):
                if abs(next_interval) > 4 or abs(cf_next_interval) > 4:
                    return False 
        return True

    def _doesnt_create_hiddens_or_parallels(self, note: Note, index: int) -> bool:
        chro_interval = note.get_chromatic_interval(self._cf.get_note(index))
        if abs(chro_interval) not in [7, 12]:
            return True 
        prev_note = self._counterpoint[index - 1]
        next_note = self._counterpoint[index + 1]
        if prev_note is not None:
            prev_interval = prev_note.get_scale_degree_interval(note)
            cf_prev_interval = self._cf.get_note(index - 1).get_scale_degree_interval(self._cf.get_note(index))
            if (prev_interval > 0 and cf_prev_interval > 0) or (prev_interval < 0 and cf_prev_interval < 0):
                return False 
        if next_note is not None:
            next_interval = note.get_scale_degree_interval(next_note)
            cf_next_interval = self._cf.get_note(index).get_scale_degree_interval(self._cf.get_note(index + 1))
            if (next_interval > 0 and cf_next_interval > 0) or (next_interval < 0 and cf_next_interval < 0):
                next_chro_interval = next_note.get_chromatic_interval(self._cf.get_note(index + 1))
                if abs(next_chro_interval) in [7, 12]:
                    return False
        return True 

    def _no_cross_relations_with_previously_added(self, note: Note) -> bool:
        for n in self._counterpoint:
            if n is not None and n.get_scale_degree_interval(note) == 1 and n.get_chromatic_interval(note) != 0: 
                return False 
        return True

    def _segment_has_legal_shape(self, seg: list[Note]) -> bool:
        if len(seg) < 3: return True 
        prev_interval = seg[0].get_scale_degree_interval(seg[1])
        for i in range(1, len(seg) - 1):
            cur_interval = seg[i].get_scale_degree_interval(seg[i + 1])
            if cur_interval > prev_interval:
                if len(seg) > 4 or cur_interval not in [3, -2] or prev_interval < -3:
                    return False 
            prev_interval = cur_interval
        return True 

    def _segment_outlines_legal_interval(self, seg: list[Note]) -> bool:
        if len(seg) < 3: return True 
        return self._valid_outline(seg[0], seg[-1])

    def _leap_chain_is_legal(self, chain: list[Note]) -> bool:
        if len(chain) < 3: return True 
        for i in range(len(chain) - 2):
            for j in range(i + 2, len(chain)):
                if not self._valid_outline(chain[i], chain[j]):
                    return False 
        return True 

    def _score_solution(self, solution: list[Note]) -> int:
        score = 0 #violations will result in increases to score
        #start by determining ratio of steps
        num_steps = 0
        num_leaps = 0
        for i in range(1, self._length):
            if abs(solution[i - 1].get_scale_degree_interval(solution[i])) == 2:
                num_steps += 1
            elif abs(solution[i - 1].get_scale_degree_interval(solution[i])) > 3:
                num_leaps += 1
        ratio = num_steps / (self._length - 1)
        if ratio > AVERAGE_STEPS_PERCENTAGE: score += math.floor((ratio - AVERAGE_STEPS_PERCENTAGE) * 20)
        elif ratio < AVERAGE_STEPS_PERCENTAGE: score += math.floor((AVERAGE_STEPS_PERCENTAGE - ratio) * 100)
        if num_leaps == 0: score += 15

        #next, find the frequency of the most repeated note
        most_frequent = 1
        for i, note in enumerate(solution):
            freq = 1
            for j in range(i + 1, self._length):
                if note.get_chromatic_interval(solution[j]) == 0:
                    freq += 1
            most_frequent = max(most_frequent, freq)
        max_acceptable = MAX_ACCEPTABLE_REPITITIONS_BASED_ON_LENGTH[self._length]
        if most_frequent > max_acceptable:
            score += (most_frequent - max_acceptable) * 15

        #next, see if sharps are follwed by an ascending step
        for i, note in enumerate(solution):
            if note.get_accidental() == ScaleOption.SHARP:
                next_interval = note.get_scale_degree_interval(solution[i + 1]) #note that a sharp will never be in the last position
                if next_interval == 3:
                    score += 5
                elif next_interval != 2:
                    score += 15

        #finally, assess the number of favored harmonic intervals 
        for i in range(1, self._length - 1):
            harmonic_interval = abs(solution[i].get_scale_degree_interval(self._cf.get_note(i)))
            if harmonic_interval == 10: score += 2
            if harmonic_interval in [5, 8]: score += 5

        return score
        



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
        if self._mode == ModeOption.AEOLIAN and new_sdg == 2:
            valid_notes.append(Note(new_sdg, new_octv, 8, accidental = ScaleOption.SHARP))
        if new_sdg in [1, 4, 5]:
            valid_notes.append(Note(new_sdg, new_octv, 8, accidental = ScaleOption.SHARP))
        return valid_notes