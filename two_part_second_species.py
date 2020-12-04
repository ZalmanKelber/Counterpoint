from random import random, shuffle
import math
from enum import Enum 

from notation_system import ModeOption, ScaleOption, Note, ModeResolver 
from cantus_firmus import CantusFirmus, GenerateCantusFirmus
from two_part_first_species import Orientation
from legal_intervals import LegalIntervals
from two_part_first_species import MAX_ACCEPTABLE_REPITITIONS_BASED_ON_LENGTH

class GenerateTwoPartSecondSpecies:

    def __init__(self, length: int = None, mode: ModeOption = None, octave: int = 4, orientation: Orientation = Orientation.ABOVE):
        self._orientation = orientation
        self._mode = mode or MODES_BY_INDEX[math.floor(random() * 6)]
        self._length = length or 8 + math.floor(random() * 5) #todo: replace with normal distribution
        self._octave = octave
        self._mr = ModeResolver(self._mode)
        gcf = GenerateCantusFirmus(self._length, self._mode, self._octave)
        cf = None 
        #if the Cantus Firmus doesn't generate, we have to try again
        #also, if we are below the Cantus Firmus, the Cantus Firmus must end stepwise
        while cf is None or (cf.get_note(self._length - 2).get_scale_degree_interval(cf.get_note(self._length - 1)) < -2 and orientation == Orientation.BELOW):
            cf = gcf.generate_cf()
        self._cantus_object = cf
        self._cantus = cf.get_notes()

        #determined through two randomly generated booleans if we will start on the offbeat 
        #or onbeat and whether the penultimate measure will be divided
        #IMPORTANT: define these in the constructor rather than at initialization otherwise we'll get length mismatches among solutions
        self._start_on_beat = True if random() > .5 else False 
        self._penult_is_whole = True if random() > .5 else False 

        #keep track of which measures are divided 
        self._divided_measures = set([i for i in range(self._length - 2 if self._penult_is_whole else self._length - 1)])

        #keep track of all indices of notes (they will be in the form (measure, beat))
        #assume measures are four beats and beats are quarter notes 
        indices = [(0, 0), (0, 2)] if self._start_on_beat else [(0, 2)]
        for i in range(1, self._length):
            indices += [(i, 0), (i, 2)] if i in self._divided_measures else [(i, 0)]
        self._all_indices = indices

    def print_counterpoint(self):
        print("  CANTUS FIRMUS:       COUNTERPOINT:")
        for i in range(self._length):
            cntpt_note = self._counterpoint[(i, 0)] if (i, 0) in self._counterpoint else "REST"
            print("  " + str(self._cantus[i]) + "  " + str(cntpt_note))
            if i in self._divided_measures:
                print("                       " + str(self._counterpoint[(i, 2)]))

    def get_optimal(self):
        if len(self._solutions) == 0:
            return None 
        optimal = self._solutions[0]
        self._map_solution_onto_counterpoint_dict(optimal)
        sol = [Note(1, 0, 4, ScaleOption.REST), self._counterpoint[(0, 2)]] if not self._start_on_beat else [self._counterpoint[(0, 0)], self._counterpoint[(0, 2)]]
        for i in range(1, self._length):
            sol.append(self._counterpoint[(i, 0)])
            if i in self._divided_measures:
                sol.append(self._counterpoint[(i, 2)])
        self.print_counterpoint()
        return [sol, self._cantus]
            
    def generate_2p2s(self):
        print("MODE = ", self._mode.value["name"])
        self._solutions = []
        def attempt():
            initialized = self._initialize()
            while not initialized:
                initialized = self._initialize()
            self._backtrack()
        attempt()
        attempts = 1
        while len(self._solutions) < 30 and attempts < 100:
            attempts += 1
            print("attempt", attempts)
            attempt()
        print("number of attempts:", attempts)
        print("number of solutions:", len(self._solutions))
        if len(self._solutions) > 0:
            solutions = self._solutions[:100]
            solutions.sort(key = lambda sol: self._score_solution(sol))
            self._solutions = solutions 

    def _initialize(self) -> bool:
        #initialize counterpoint data structure, that will map indices to notes
        counterpoint = {}
        for index in self._all_indices: counterpoint[index] = None 

        #initialize range to 8.  we'll modify it based on probability
        vocal_range = 8 
        range_alteration = random()
        if range_alteration < .1: vocal_range -= math.floor(random() * 3)
        elif range_alteration > .5: vocal_range += math.floor(random() * 3)

        cantus_final = self._cantus[0]
        cantus_first_interval = cantus_final.get_scale_degree_interval(self._cantus[1])
        cantus_last_interval = self._cantus[-2].get_scale_degree_interval(self._cantus[-1])

        first_note, last_note, penult_note = None, None, None 
        highest_so_far, lowest_so_far = None, None
        lowest, highest = None, None
        if self._orientation == Orientation.ABOVE:
            start_interval_options = [1, 5, 8] if cantus_first_interval < 0 and self._cantus_object.get_upward_range() < 3 else [5, 8]
            shuffle(start_interval_options)
            start_interval = start_interval_options[0]
            first_note = self._get_default_note_from_interval(cantus_final, start_interval)
            highest_so_far, lowest_so_far = first_note, first_note
            last_interval_options = [1, 1, 5] if start_interval == 1 else [8, 8, 5] if start_interval == 8 else [1, 1, 8, 8, 5]
            if self._cantus[-2].get_scale_degree_interval(self._cantus[-1]) < 0: 
                if 1 in last_interval_options: last_interval_options.remove(1)
            if cantus_last_interval == 5:
                last_interval_options = [5]
            if cantus_last_interval == 4: 
                if 5 in last_interval_options: last_interval_options.remove(5)
                if len(last_interval_options) == 0:
                    last_interval_options = [8]
                    first_note = self._get_default_note_from_interval(cantus_final, 8)
                    highest_so_far, lowest_so_far = first_note, first_note
            shuffle(last_interval_options)
            last_interval = last_interval_options[0]
            last_note = self._get_default_note_from_interval(cantus_final, last_interval)
            if highest_so_far.get_scale_degree_interval(last_note) > 1: highest_so_far = last_note
            if lowest_so_far.get_scale_degree_interval(last_note) < 0: lowest_so_far = last_note
            penult_note = self._get_leading_tone_of_note(last_note) if cantus_last_interval == -2 else self._get_default_note_from_interval(last_note, 2)
            if last_interval == 5: self._mr.make_default_scale_option(penult_note)
            if highest_so_far.get_scale_degree_interval(penult_note) > 1: highest_so_far = last_note
            if lowest_so_far.get_scale_degree_interval(penult_note) < 0: lowest_so_far = last_note
            #we have to figure out how many lower notes it is possible to assign
            gap_so_far = self._cantus_object.get_highest_note().get_scale_degree_interval(lowest_so_far) 
            leeway = vocal_range - lowest_so_far.get_scale_degree_interval(highest_so_far) + 1
            allowance = 1 if first_note.get_scale_degree_interval(last_note) == 1 and penult_note.get_scale_degree_interval(last_note) > 0 else 0
            max_available_lower_scale_degrees = min(max(1, gap_so_far + 2 if gap_so_far > 0 else gap_so_far + 4), leeway - allowance)
            interval_to_lowest = math.ceil(random() * max_available_lower_scale_degrees)
            lowest = self._get_default_note_from_interval(lowest_so_far, interval_to_lowest * -1) if interval_to_lowest > 1 else lowest_so_far 
            highest = self._get_default_note_from_interval(lowest, vocal_range)
            if vocal_range == 8:
                highest.set_accidental(lowest.get_accidental())
            while ( lowest.get_chromatic_interval(first_note) % 12 == 6 or first_note.get_chromatic_interval(highest) % 12 == 6 or 
                lowest.get_chromatic_interval(last_note) % 12 == 6 or last_note.get_chromatic_interval(highest) % 12 == 6 or 
                lowest.get_chromatic_interval(highest) % 12 == 6):
                interval_to_lowest = math.ceil(random() * max_available_lower_scale_degrees)
                lowest = self._get_default_note_from_interval(lowest_so_far, interval_to_lowest * -1) if interval_to_lowest > 1 else lowest_so_far 
                highest = self._get_default_note_from_interval(lowest, vocal_range)
                if vocal_range == 8:
                    highest.set_accidental(lowest.get_accidental())
            
        if self._orientation == Orientation.BELOW:
            if self._cantus_object.get_downward_range() >= 3 or cantus_first_interval < 0 or cantus_last_interval < 0 or random() > .5:
                first_note = self._get_default_note_from_interval(cantus_final, -8)
            else:
                first_note = self._get_default_note_from_interval(cantus_final, -8)
            last_note = first_note 
            if cantus_last_interval > 0:
                penult_note = self._get_default_note_from_interval(last_note, 2)
                lowest_so_far, highest_so_far = last_note, penult_note
            else:
                penult_note = self._get_leading_tone_of_note(last_note)
                lowest_so_far, highest_so_far = penult_note, last_note
            leeway = vocal_range - 1
            gap_so_far = highest_so_far.get_scale_degree_interval(self._cantus_object.get_lowest_note()) 
            max_available_higher_scale_degrees = min(leeway, max(1, gap_so_far + 2 if gap_so_far > 0 else gap_so_far + 4))
            allowance = 1 if cantus_last_interval > 0 else 0
            interval_to_highest = math.floor(random() * (max_available_higher_scale_degrees - allowance)) + 1 + allowance 
            highest = self._get_default_note_from_interval(highest_so_far, interval_to_highest)
            lowest = self._get_default_note_from_interval(highest, vocal_range * -1)
            if lowest.get_scale_degree_interval(penult_note) == 1:
                penult_note.set_accidental(lowest.get_accidental())
            while (lowest.get_chromatic_interval(first_note) % 12 == 6 or first_note.get_chromatic_interval(highest) % 12 == 6 or 
                lowest.get_chromatic_interval(highest) % 12 == 6):
                interval_to_highest = math.floor(random() * (max_available_higher_scale_degrees - allowance)) + 1 + allowance 
                highest = self._get_default_note_from_interval(highest_so_far, interval_to_highest)
                lowest = self._get_default_note_from_interval(highest, vocal_range * -1)
                if lowest.get_scale_degree_interval(penult_note) == 1:
                    penult_note.set_accidental(lowest.get_accidental())

        #add counterpoint dict and remaining indices 
        counterpoint[self._all_indices[0]] = first_note
        counterpoint[self._all_indices[-2]] = penult_note
        counterpoint[self._all_indices[-1]] = last_note
        self._counterpoint = counterpoint
        self._remaining_indices = self._all_indices[1: -2]

        #generate valid pitches 
        valid_pitches = [lowest]
        for i in range(2, vocal_range): #we don't include the highest note
            valid_pitches += self._get_notes_from_interval(lowest, i)
        self._valid_pitches = valid_pitches


        #add highest and lowest notes if they're not already present 
        if highest_so_far.get_scale_degree_interval(highest) != 1:
            if not self._place_highest(highest):
                return False 
        if lowest.get_scale_degree_interval(lowest_so_far) != 1:
            if not self._place_lowest(lowest):
                return False 
        self._remaining_indices.sort(reverse = True)
        return True 

    def _place_highest(self, note: Note) -> bool:
        possible_indices = self._remaining_indices[:]
        if self._length % 2 == 1:
            possible_indices.remove((math.floor(self._length / 2), 0))
        shuffle(possible_indices)
        index = None
        while len(possible_indices) > 0:
            index = possible_indices.pop()
            if not self._passes_insertion_check(note, index):
                continue 
            #if it passes insertion checks, make sure last two intervals are not invalid 
            next_note = self._get_next_note(index)
            if next_note is not None:
                last_note = self._counterpoint[(self._length - 1, 0)]
                if next_note.get_scale_degree_interval(last_note) == -2 and note.get_scale_degree_interval(next_note) < -2:
                    continue 
            break 
        if len(possible_indices) == 0:
            return False 
        self._counterpoint[index] = note 
        self._remaining_indices.remove(index)
        return True 

    def _place_lowest(self, note: Note) -> bool:
        possible_indices = self._remaining_indices[:]
        shuffle(possible_indices)
        index = None
        while len(possible_indices) > 0:
            index = possible_indices.pop()
            if not self._passes_insertion_check(note, index):
                continue 
            #if it passes insertion checks, find a span it may be attached to and evaluate
            span = [note]
            lower_index, upper_index = self._get_prev_index(index), self._get_next_index(index)
            while lower_index is not None and self._counterpoint[lower_index] is not None:
                span = [self._counterpoint[lower_index]] + span 
                lower_index = self._get_prev_index(lower_index)
            while upper_index is not None and self._counterpoint[upper_index] is not None:
                span.append(self._counterpoint[upper_index])
                upper_index = self._get_next_index(upper_index)
            if not self._span_is_valid(span, check_beginning = False, check_ending = False):
                continue 
            break
        if len(possible_indices) == 0:
            return False 
        self._counterpoint[index] = note 
        self._remaining_indices.remove(index)
        return True 

    def _backtrack(self) -> None:
        if len(self._solutions) >= 50: return
        if len(self._remaining_indices) == 0:
            sol = []
            for i in range(len(self._all_indices)):
                sol.append(self._counterpoint[self._all_indices[i]])
            if self._passes_final_checks(sol):
                self._solutions.append(sol)
            return 
        index = self._remaining_indices.pop() 
        candidates = list(filter(lambda n: self._passes_insertion_check(n, index), self._valid_pitches))
        for candidate in candidates:
            self._counterpoint[index] = candidate
            if self._current_chain_is_legal():
                self._backtrack()
        self._counterpoint[index] = None 
        self._remaining_indices.append(index)

    def _get_leading_tone_of_note(self, note: Note) -> Note:
        lt = self._get_default_note_from_interval(note, -2)
        if lt.get_scale_degree() in [1, 4, 5] or (lt.get_scale_degree() == 2 and self._mode == ModeOption.AEOLIAN):
            lt.set_accidental(ScaleOption.SHARP)
        if lt.get_scale_degree() == 7:
            lt.set_accidental(ScaleOption.NATURAL)
        return lt

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
        else:
            while new_sdg > 7:
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

    def _is_valid_adjacent(self, note1: Note, note2: Note) -> bool:
        sdg_interval = note1.get_scale_degree_interval(note2)
        if (note1.get_accidental() == ScaleOption.SHARP or note2.get_accidental() == ScaleOption.SHARP) and abs(sdg_interval) > 3:
            return False 
        #if a sharp is not followed by a step up, we'll give it an arbitrary 50% chance of passing
        is_leading_tone = note1.get_accidental == ScaleOption.SHARP or (note1.get_scale_degree() == 7 and self._mode in [ModeOption.DORIAN, ModeOption.LYDIAN])
        if sdg_interval != 2 and is_leading_tone and random() > .5:
            return False 

        chro_interval = note1.get_chromatic_interval(note2)
        if ( sdg_interval in LegalIntervals["adjacent_melodic_scalar"] 
            and chro_interval in LegalIntervals["adjacent_melodic_chromatic"]
            and (sdg_interval, chro_interval) not in LegalIntervals["forbidden_combinations"] ):
            return True 
        return False 

    def _is_valid_outline(self, note1: Note, note2: Note) -> bool:
        sdg_interval = note1.get_scale_degree_interval(note2)
        chro_interval = note1.get_chromatic_interval(note2)
        if ( sdg_interval in LegalIntervals["outline_melodic_scalar"] 
            and chro_interval in LegalIntervals["outline_melodic_chromatic"]
            and (sdg_interval, chro_interval) not in LegalIntervals["forbidden_combinations"] ):
            return True 
        return False 

    def _is_valid_harmonically(self, note1: Note, note2: Note) -> bool:
        sdg_interval = note1.get_scale_degree_interval(note2)
        chro_interval = note1.get_chromatic_interval(note2)
        if ( sdg_interval in LegalIntervals["harmonic_scalar"] 
            and chro_interval in LegalIntervals["harmonic_chromatic"]
            and (sdg_interval, chro_interval) not in LegalIntervals["forbidden_combinations"] ):
            return True 
        return False 

    def _is_unison(self, note1: Note, note2: Note) -> bool:
        return note1.get_scale_degree_interval(note2) == 1 and note1.get_chromatic_interval(note2) == 0 

    def _get_prev_note(self, index: tuple) -> Note:
        prev_index = self._get_prev_index(index)
        return None if prev_index is None else self._counterpoint[prev_index]

    def _get_next_note(self, index: tuple) -> Note:
        next_index = self._get_next_index(index)
        return None if next_index is None else self._counterpoint[next_index]

    def _get_prev_index(self, index: tuple) -> tuple:
        i = self._all_indices.index(index)
        if i == 0: return None
        return self._all_indices[i - 1]

    def _get_next_index(self, index: tuple) -> tuple:
        i = self._all_indices.index(index)
        if i == len(self._all_indices) - 1: return None 
        return self._all_indices[i + 1]

    def _passes_insertion_check(self, note: Note, index: tuple) -> bool:
        (i, j) = index
        prev_note, next_note = self._get_prev_note(index), self._get_next_note(index)
        if prev_note is not None and not self._is_valid_adjacent(prev_note, note): return False 
        if next_note is not None and not self._is_valid_adjacent(note, next_note): return False 
        if not self._valid_harmonic_insertion(note, index): return False 
        if not self._doesnt_create_parallels(note, index): return False 
        if not self._no_large_parallel_leaps(note, index): return False 
        if not self._no_cross_relations_with_cantus_firmus(note, index): return False 
        if not self._no_octave_leap_with_perfect_harmonic_interval(note, index): return False 
        return True 

    def _valid_harmonic_insertion(self, note: Note, index: tuple) -> bool:
        (i, j) = index
        cf_note = self._cantus[i]
        if self._is_valid_harmonically(note, cf_note): 
            if j == 0:
                prev_note, cf_prev = self._counterpoint[(i - 1, 2)], self._cantus[i - 1]
                if prev_note is not None and not self._is_valid_harmonically(prev_note, cf_prev):
                    if (i - 1, 0) in self._counterpoint and self._counterpoint[(i - 1, 0)].get_scale_degree_interval(prev_note) != prev_note.get_scale_degree_interval(note):
                        return False 
            return True 
        if j == 0: return False 
        if cf_note.get_chromatic_interval(note) == 0: return True 
        prev_note = self._counterpoint[(i, 0)]
        if prev_note is None: return False #the highest or lowest note cannot be a passing tone 
        if abs(prev_note.get_scale_degree_interval(note)) != 2: return False 
        next_note = self._counterpoint[(i + 1, 0)]
        if next_note is None: return True 
        return note.get_scale_degree_interval(next_note) == prev_note.get_scale_degree_interval(note)


    def _doesnt_create_parallels(self, note: Note, index: tuple) -> bool:
        (i, j) = index 
        cf_note, next_note, cf_next = self._cantus[i], self._counterpoint[(i + 1, 0)], self._cantus[i + 1]
        if next_note is not None and abs(next_note.get_chromatic_interval(cf_next)) in [0, 7, 12, 19]:
            #next measure is a perfect interval.  check for parallels first 
            if note.get_chromatic_interval(cf_note) == next_note.get_chromatic_interval(cf_next):
                return False 
            #check for hidden intervals unless top voice moves by step
            if ( j == 2 and ((note.get_scale_degree_interval(next_note) > 0 and cf_note.get_scale_degree_interval(cf_next) > 0) or 
                (note.get_scale_degree_interval(next_note) < 0 and cf_note.get_scale_degree_interval(cf_next) < 0))):
                if ( (cf_next.get_scale_degree_interval(next_note) > 0 and abs(note.get_scale_degree_interval(next_note)) != 2) or 
                    (cf_next.get_scale_degree_interval(next_note) < 0 and abs(cf_note.get_scale_degree_interval(cf_next)) != 2)):
                    return False 
        #if j is 2 we don't have to check what comes before 
        if j == 0 and note.get_chromatic_interval(cf_note) in [0, 7, 12, 19]:
            cf_prev = self._cantus[i - 1]
            #check previous downbeat if it exists
            if i - 1 != 0 or self._start_on_beat:
                prev_downbeat = self._counterpoint[(i - 1, 0)]
                if prev_downbeat is not None and note.get_chromatic_interval(cf_note) == prev_downbeat.get_chromatic_interval(cf_prev):
                    return False
            #previous weak beat will always exist when we check an insertion 
            prev_note = self._counterpoint[(i - 1, 2)]
            if prev_note is not None and note.get_chromatic_interval(cf_note) == prev_note.get_chromatic_interval(cf_prev):
                return False
            #check for hiddens 
            if (prev_note is not None and ((prev_note.get_scale_degree_interval(note) > 0 and cf_prev.get_scale_degree_interval(cf_note) > 0) or 
                (prev_note.get_scale_degree_interval(note) < 0 and cf_prev.get_scale_degree_interval(cf_note) < 0))):
                if ( (cf_note.get_scale_degree_interval(note) > 0 and abs(prev_note.get_scale_degree_interval(note)) != 2) or 
                    (cf_note.get_scale_degree_interval(note) < 0 and abs(cf_prev.get_scale_degree_interval(cf_note)) != 2)):
                    return False 
        return True 

    def _no_large_parallel_leaps(self, note: Note, index: tuple) -> bool:
        (i, j) = index 
        cf_prev, cf_note, cf_next = self._cantus[i - 1], self._cantus[i], self._cantus[i + 1]
        if j == 2:
            next_note = self._counterpoint[(i + 1, 0)]
            if next_note is not None:
                next_interval, cf_next_interval = note.get_scale_degree_interval(next_note), cf_note.get_scale_degree_interval(cf_next)
                if ((abs(next_interval) > 2 and abs(cf_next_interval) > 2 and (abs(next_interval) > 4 or abs(cf_next_interval) > 4) and 
                    ((next_interval > 0 and cf_next_interval > 0) or (next_interval < 0 and cf_next_interval < 0)))):
                    return False 
        else:
            prev_note = self._counterpoint[(i - 1, 2)] #this index will always exist when we check this 
            if prev_note is not None:
                prev_interval, cf_prev_interval = prev_note.get_scale_degree_interval(note), cf_prev.get_scale_degree_interval(cf_note)
                if ((abs(prev_interval) > 2 and abs(cf_prev_interval) > 2 and (abs(prev_interval) > 4 or abs(cf_prev_interval) > 4) and 
                    ((prev_interval > 0 and cf_prev_interval > 0) or (prev_interval < 0 and cf_prev_interval < 0)))):
                    return False 
        return True 

    def _no_cross_relations_with_cantus_firmus(self, note: Note, index: tuple) -> bool:
        (i, j) = index
        cf_note = self._cantus[i - 1 if j == 0 else i + 1]
        if abs(cf_note.get_scale_degree_interval(note)) in [1, 8]:
            return cf_note.get_accidental() == note.get_accidental()
        return True 

    def _no_octave_leap_with_perfect_harmonic_interval(self, note: Note, index: tuple) -> bool:
        (i, j) = index 
        if i not in self._divided_measures or abs(self._cantus[i].get_scale_degree_interval(note)) not in [1, 5, 8, 12]:
            return True 
        other_note = self._counterpoint[(i, 0 if j == 2 else 2)]
        if other_note is not None and abs(note.get_scale_degree_interval(other_note)) == 8: return False 
        return True 

    def _current_chain_is_legal(self) -> bool:
        current_chain = []
        index = (0, 0) if self._start_on_beat else (0, 2)
        while index is not None and self._counterpoint[index] is not None:
            current_chain.append(self._counterpoint[index])
            index = self._get_next_index(index)
        result = self._span_is_valid(current_chain)
        return result

    def _span_is_valid(self, span: list[Note], check_beginning: bool = True, check_ending: bool = False) -> bool:
        if len(span) < 3: return True 
        if self._remaining_indices == 0: check_ending = True 
        if not self._segments_and_chains_are_legal(span, check_beginning, check_ending): return False 
        if not self._no_illegal_repetitions(span): return False 
        if not self._ascending_intervals_handled(span): return False 
        if not self._no_nearby_cross_relations(span): return False 
        return True 

    def _segments_and_chains_are_legal(self, span: list[Note], check_beggining: bool, check_ending: bool) -> bool:
        intervals = [span[i - 1].get_scale_degree_interval(span[i]) for i in range(1, len(span))]
        for i in range(1, len(intervals)):
            if ((intervals[i - 1] > 0 and intervals[i] > 0) or (intervals[i - 1] < 0 and intervals[i] < 0)) and intervals[i] > intervals[i - 1]:
                return False 
        span_indices_ending_segments = [0] if check_beggining else []
        for i in range(1, len(intervals)):
            if ((intervals[i - 1] > 0 and intervals[i] < 0) or (intervals[i - 1] < 0 and intervals[i] > 0)):
                span_indices_ending_segments.append(i)
        span_indices_ending_segments += [len(span) - 1] if check_ending else []
        for i in range(1, len(span_indices_ending_segments)):
            start_note, end_note = span[span_indices_ending_segments[i - 1]], span[span_indices_ending_segments[i]]
            if not self._is_valid_outline(start_note, end_note): return False 
        return True 

    def _no_illegal_repetitions(self, span: list[Note]) -> bool:
        for i in range(len(span) - 5):
            count = 1
            for j in range(i + 1, i + 6):
                if span[i].get_scale_degree_interval(span[j]) == 1: count += 1
            if count >= 3: return False 
        for i in range(len(span) - 3):
            if span[i].get_scale_degree_interval(span[i + 2]) == 1 and span[i + 1].get_scale_degree_interval(span[i + 3]) == 1:
                return False 
        return True 

    def _no_nearby_cross_relations(self, span: list[Note]) -> bool:
        for i in range(len(span) - 2):
            if span[i].get_scale_degree_interval(span[i + 2]) == 1 and span[i].get_chromatic_interval(span[i + 2]):
                return False 
        return True 

    def _ascending_intervals_handled(self, span: list[Note]) -> bool:
        for i in range(1, len(span) - 1):
            if span[i - 1].get_chromatic_interval(span[i]) == 8 and span[i].get_chromatic_interval(span[i + 1]) != -1:
                return False 
            elif span[i - 1].get_scale_degree_interval(span[i]) > 3 and span[i].get_scale_degree_interval(span[i + 1]) != -2 and random() > .5:
                return False 
        return True 

    def _passes_final_checks(self, solution: list[Note]) -> bool:
        return self._handles_ascending_intervals(solution) and self._handles_sequences(solution)

    def _handles_ascending_intervals(self, solution: list[Note]) -> bool:
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

    def _handles_sequences(self, solution: list[Note]) -> bool:
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
                if random() < .8:
                    return False
        #check if three exact notes repeat
        for i in range(len(solution) - 5):
            for j in range(i + 3, self._length - 2):
                if solution[i].get_chromatic_interval(solution[j]) == 0 and solution[i + 1].get_chromatic_interval(solution[j + 1]) == 0 and solution[i + 2].get_chromatic_interval(solution[j + 2]) == 0:
                    return False 
        return True

    def _map_solution_onto_counterpoint_dict(self, solution: list[Note]) -> None:
        for i, note in enumerate(solution):
            (measure, beat) = self._all_indices[i]
            if measure in self._divided_measures:
                note.set_duration(4)
            self._counterpoint[(measure, beat)] = note

    def _score_solution(self, solution: list[Note]) -> int:
        score = 0 #violations will result in increases to score
        #start by determining ratio of steps
        num_steps = 0
        num_leaps = 0
        for i in range(1, len(solution)):
            if abs(solution[i - 1].get_scale_degree_interval(solution[i])) == 2:
                num_steps += 1
            elif abs(solution[i - 1].get_scale_degree_interval(solution[i])) > 3:
                num_leaps += 1
        ratio = num_steps / (len(solution) - 1)
        if ratio > .712: score += math.floor((ratio - .712) * 20)
        elif ratio < .712: score += math.floor((.712 - ratio) * 100)
        if num_leaps == 0: score += 15

        #next, find the frequency of the most repeated note
        most_frequent = 1
        for i, note in enumerate(solution):
            freq = 1
            for j in range(i + 1, len(solution)):
                if note.get_chromatic_interval(solution[j]) == 0:
                    freq += 1
            most_frequent = max(most_frequent, freq)
        max_acceptable = MAX_ACCEPTABLE_REPITITIONS_BASED_ON_LENGTH[len(solution)]
        if most_frequent > max_acceptable:
            score += (most_frequent - max_acceptable) * 15

        #finally, assess the number of favored harmonic intervals 
        # if len(solution) != len(self._all_indices):
        #     self.print_counterpoint()
        #     print(self._all_indices)
        for i, note in enumerate(solution):
            (measure, beat) = self._all_indices[i]
            if beat == 0:
                harmonic_interval = abs(solution[i].get_scale_degree_interval(self._cantus[measure]))
                if harmonic_interval in [5, 12]: score += 40
                if harmonic_interval in [1, 8]: score += 10
        return score




        
