import sys
sys.path.insert(0, "/Users/alexkelber/Development/timeout-decorator-0.5.0")
import timeout_decorator

from random import random, shuffle
import math
from time import time

from notation_system import ModeOption, ScaleOption, Note, ModeResolver 
from cantus_firmus import CantusFirmus, GenerateCantusFirmus
from two_part_first_species import Orientation
from legal_intervals import LegalIntervalsThirdSpecies, MaxAcceptableRepetitions

class GenerateTwoPartThirdSpecies:

    def __init__(self, length: int = None, mode: ModeOption = None, octave: int = 4, orientation: Orientation = Orientation.ABOVE):
        self._orientation = orientation
        self._mode = mode or ModeOption.DORIAN
        self._length = length or 8 + math.floor(random() * 5) #todo: replace with normal distribution
        self._octave = octave
        self._mr = ModeResolver(self._mode)
        gcf = GenerateCantusFirmus(self._length, self._mode, self._octave)
        cf = None 
        #if the Cantus Firmus doesn't generate, we have to try again
        #also, if we are below the Cantus Firmus, the Cantus Firmus must end stepwise
        while cf is None or abs(cf.get_note(self._length - 2).get_scale_degree_interval(cf.get_note(self._length - 1))) > 2:
            cf = gcf.generate_cf()
        self._cantus_object = cf
        self._cantus = cf.get_notes()

        #determined through two randomly generated booleans if we will start on the offbeat 
        #or onbeat and whether the penultimate measure will be divided
        #IMPORTANT: define these in the constructor rather than at initialization otherwise we'll get length mismatches among solutions
        self._start_on_beat = True if random() < .7 else False 
        self._penult_is_whole = True if random() < .7 else False 

        #keep track of which measures are divided 
        self._divided_measures = set([i for i in range(self._length - 2 if self._penult_is_whole else self._length - 1)])

        #keep track of all indices of notes (they will be in the form (measure, beat))
        #assume measures are four beats and beats are quarter notes 
        indices = [(0, 0), (0, 1), (0, 2), (0, 3)] if self._start_on_beat else [(0, 1), (0, 2), (0, 3)]
        for i in range(1, self._length):
            indices += [(i, 0), (i, 1), (i, 2), (i, 3)] if i in self._divided_measures else [(i, 0)]
        self._all_indices = indices

    def print_counterpoint(self):
        print("  CANTUS FIRMUS:       COUNTERPOINT:")
        for i in range(self._length):
            cntpt_note = self._counterpoint[(i, 0)] if (i, 0) in self._counterpoint else "REST"
            print("  " + str(self._cantus[i]) + "  " + str(cntpt_note))
            if i in self._divided_measures:
                for j in range(1, 4):
                    print("                       " + str(self._counterpoint[(i, j)]))

    def get_optimal(self):
        if len(self._solutions) == 0:
            return None 
        optimal = self._solutions[0]
        self._map_solution_onto_counterpoint_dict(optimal)
        sol = [Note(1, 0, 2, ScaleOption.REST)] if not self._start_on_beat else [self._counterpoint[(0, 0)]]
        for i in range(self._length):
            if i != 0:
                sol.append(self._counterpoint[(i, 0)])
            if i in self._divided_measures:
                for j in range(1, 4):
                    sol.append(self._counterpoint[(i, j)])
        self.print_counterpoint()
        return [sol, self._cantus]
            
    def generate_2p3s(self):
        start_time = time()
        print("MODE = ", self._mode.value["name"])
        self._solutions = []
        @timeout_decorator.timeout(20)
        def attempt():
            initialized = self._initialize()
            while not initialized:
                print("initialization failed")
                initialized = self._initialize()
            self._backtrack()
        attempt()
        attempts = 0
        while len(self._solutions) < 30 and time() - start_time < 20:
            print("attempt", attempts)
            try:
                attempt()
                attempts += 1
            except: 
                print("attempt did not complete")
        print("number of attempts:", attempts)
        print("number of solutions:", len(self._solutions))
        if len(self._solutions) > 0:
            self._solutions.sort(key = lambda sol: self._score_solution(sol)) 

    def _initialize(self) -> bool:
        #initialize counterpoint data structure, that will map indices to notes
        counterpoint = {}
        for index in self._all_indices: counterpoint[index] = None 

        #initialize range to 8.  we'll modify it based on probability
        vocal_range = 10
        range_alteration = random()
        if range_alteration < .1 and self._length < 11: vocal_range = 9
        else: vocal_range += math.floor(random() * 3)

        cantus_final = self._cantus[0]
        cantus_last_interval = self._cantus[-2].get_scale_degree_interval(self._cantus[-1])

        #find first, penultimate, last, lowest and highest notes 
        lowest, highest = None, None
        start_interval = 1 if random() < .5 else 8
        last_interval = start_interval if random() < .5 else 1 if random() < .5 else 8
        first_note = lowest_so_far = highest_so_far = self._get_default_note_from_interval(cantus_final, start_interval)
        last_note = self._get_default_note_from_interval(cantus_final, last_interval)
        if highest_so_far.get_scale_degree_interval(last_note) > 1: highest_so_far = last_note
        if lowest_so_far.get_scale_degree_interval(last_note) < 0: lowest_so_far = last_note
        penult_note = self._get_leading_tone_of_note(last_note) if cantus_last_interval == -2 else self._get_default_note_from_interval(last_note, 2)
        if cantus_last_interval == -2 and self._orientation == Orientation.BELOW and self._mode != ModeOption.PHRYGIAN and self._length - 2 in self._divided_measures and random() < .3:
            penult_note = self._get_default_note_from_interval(last_note, -4)
        #if the highest note is equal to two notes, increase it to make it legal
        if highest_so_far.get_scale_degree_interval(penult_note) > 1: 
            highest_so_far = penult_note
        elif start_interval == last_interval: highest_so_far = self._get_default_note_from_interval(highest_so_far, 2)
        if lowest_so_far.get_scale_degree_interval(penult_note) < 0: lowest_so_far = penult_note
        leeway = lowest_so_far.get_scale_degree_interval(highest_so_far) + 1 
        gap = self._cantus_object.get_highest_note().get_scale_degree_interval(lowest_so_far) if self._orientation == Orientation.ABOVE else highest_so_far.get_scale_degree_interval(self._cantus_object.get_lowest_note())
        interval_to_end_of_range = max(math.floor(random() * leeway), gap) + 1
        if self._orientation == Orientation.ABOVE:
            if interval_to_end_of_range != 1: interval_to_end_of_range *= -1
            lowest = self._get_default_note_from_interval(lowest_so_far, interval_to_end_of_range)
            highest = self._get_default_note_from_interval(lowest, vocal_range)
        else:
            highest = self._get_default_note_from_interval(highest_so_far, interval_to_end_of_range)
            lowest = self._get_default_note_from_interval(highest, vocal_range * -1)
        #there is a small chance we've exceed our range in the BELOW orientation
        if lowest_so_far.get_scale_degree_interval(lowest) > 0: lowest = lowest_so_far

        #add counterpoint dict and remaining indices 
        first_note.set_duration(2)
        last_note.set_duration(16)
        if self._length - 2 in self._divided_measures:
            penult_note.set_duration(2)
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
        note = Note(note.get_scale_degree(), note.get_octave(), 2, note.get_accidental())
        possible_indices = self._remaining_indices[:]
        #in the third species, having the highest note in the middle is permissible 
        shuffle(possible_indices)
        index = None
        while len(possible_indices) > 0:
            (bar, beat) = possible_indices.pop()
            if not self._passes_insertion_check(note, (bar, beat)):
                continue 
            #in third species counterpoint, highest note can never be dissonant 
            if not self._is_valid_harmonically(note, self._cantus[bar]):
                continue
            #if it passes insertion checks, make sure last two intervals are not invalid 
            next_note = self._get_next_note((bar, beat))
            if next_note is not None:
                last_note = self._counterpoint[(self._length - 1, 0)]
                #if highest -> next is a leap, then highest -> last must be 2nd or 3rd 
                if note.get_scale_degree_interval(last_note) not in [-2, -3]:
                    continue
            break 
        if len(possible_indices) == 0:
            return False 
        self._counterpoint[(bar, beat)] = note 
        self._remaining_indices.remove((bar, beat))
        return True 

    def _place_lowest(self, note: Note) -> bool:
        note = Note(note.get_scale_degree(), note.get_octave(), 2, note.get_accidental())
        possible_indices = self._remaining_indices[:]
        shuffle(possible_indices)
        index = None
        while len(possible_indices) > 0:
            index = possible_indices.pop()
            if not self._passes_insertion_check(note, index):
                continue 
            #if it passes insertion checks, we won't check for span checks (handled later
            break
        if len(possible_indices) == 0:
            return False 
        self._counterpoint[index] = note 
        self._remaining_indices.remove(index)
        return True 

    def _backtrack(self) -> None:
        if len(self._solutions) >= 30: return
        if len(self._remaining_indices) == 0:
            print("found possible solution!")
            sol = []
            for i in range(len(self._all_indices)):
                sol.append(self._counterpoint[self._all_indices[i]])
            if self._passes_final_checks(sol):
                print("FOUND SOLUTION!")
                self._solutions.append(sol)
            return 
        (bar, beat) = self._remaining_indices.pop() 
        candidates = list(filter(lambda n: self._passes_insertion_check(n, (bar, beat)), self._valid_pitches))
        for candidate in candidates:
            candidate_copy = Note(candidate.get_scale_degree(), candidate.get_octave(), 8, candidate.get_accidental())
            if bar in self._divided_measures: candidate_copy.set_duration(2)
            self._counterpoint[(bar, beat)] = candidate_copy
            if self._current_chain_is_legal():
                self._backtrack()
        self._counterpoint[(bar, beat)] = None 
        self._remaining_indices.append((bar, beat))

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
        while new_sdg < 1:
            new_octv -= 1
            new_sdg += 7
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
        if ( sdg_interval in LegalIntervalsThirdSpecies["adjacent_melodic_scalar"] 
            and chro_interval in LegalIntervalsThirdSpecies["adjacent_melodic_chromatic"]
            and (sdg_interval, chro_interval) not in LegalIntervalsThirdSpecies["forbidden_combinations"] ):
            return True 
        return False 

    def _is_valid_outline(self, note1: Note, note2: Note) -> bool:
        sdg_interval = note1.get_scale_degree_interval(note2)
        chro_interval = note1.get_chromatic_interval(note2)
        if ( sdg_interval in LegalIntervalsThirdSpecies["outline_melodic_scalar"] 
            and chro_interval in LegalIntervalsThirdSpecies["outline_melodic_chromatic"]
            and (sdg_interval, chro_interval) not in LegalIntervalsThirdSpecies["forbidden_combinations"] ):
            return True 
        return False 

    def _is_valid_harmonically(self, note1: Note, note2: Note) -> bool:
        sdg_interval = note1.get_scale_degree_interval(note2)
        chro_interval = note1.get_chromatic_interval(note2)
        if ( sdg_interval in LegalIntervalsThirdSpecies["harmonic_scalar"] 
            and chro_interval in LegalIntervalsThirdSpecies["harmonic_chromatic"]
            and (sdg_interval, chro_interval) not in LegalIntervalsThirdSpecies["forbidden_combinations"] ):
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
        # print("passes melodic checks")
        if not self._valid_harmonic_insertion(note, index): return False 
        # print("passes harmonic checks")
        if not self._doesnt_create_parallels(note, index): return False 
        # print("passes parallels and hidden checks")
        if not self._no_large_parallel_leaps(note, index): return False 
        # print("passes parallel motion checks")
        if not self._no_cross_relations_with_cantus_firmus(note, index): return False 
        # print("passes cross relations checks")
        if not self._no_ascending_leaps_on_accented_beats(note, index): return False 
        # print("passes ascending leaps checks")
        return True 

    def _valid_harmonic_insertion(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        cf_note = self._cantus[bar]
        #cannot be unison on downbeat
        if self._is_unison(note, cf_note) and beat == 0: return False 
        #get notes we'll need to examine
        prev_note, next_note = self._get_prev_note(index), self._get_next_note(index)
        prev_index, next_index = self._get_prev_index(index), self._get_next_index(index)
        note_before_prev = self._get_prev_note(prev_index) if prev_index is not None else None
        note_after_next = self._get_next_note(next_index) if next_index is not None else None 
        #if we're on a weak beat, check for dissonance
        if beat % 2 == 1:
            if not self._is_valid_harmonically(note, cf_note):
                if prev_note is not None and abs(prev_note.get_scale_degree_interval(note)) != 2:
                    return False 
                if next_note is not None and note.get_scale_degree_interval(next_note) not in [-3, -2, 2]:
                    return False 
                if prev_note is not None and next_note is not None:
                    if prev_note.get_scale_degree_interval(note) == 2 and note.get_scale_degree_interval(next_note) != 2:
                        return False 
                    if prev_note.get_scale_degree_interval(note) == -2 and note.get_scale_degree_interval(next_note) == -3:
                        if note_after_next is not None and next_note.get_scale_degree_interval(note_after_next) != 2:
                            return False 
            #if the previous three notes are the beginning of a cambiata, make sure it's properly handled
            if note_before_prev is not None and prev_note is not None:
                if note_before_prev.get_scale_degree_interval(prev_note) == -3 and prev_note.get_scale_degree_interval(note) != 2:
                    note_to_check = cf_note if beat >= 3 else self._cantus[bar - 1]
                    if not self._is_valid_harmonically(note_to_check, note_before_prev):
                        return False 
        else:
            #if we're on an accented beat, it cannot be dissonant 
            if not self._is_valid_harmonically(note, cf_note):
                return False 
            #check for any previously unhandled dissonances previously
            if prev_note is not None:
                note_to_check = cf_note if beat >= 2 else self._cantus[bar - 1]
                if not self._is_valid_harmonically(note_to_check, prev_note):
                    if prev_note.get_scale_degree_interval(note) not in [-3, -2, 2]:
                        return False 
                    if note_before_prev is not None:
                        if note_before_prev.get_scale_degree_interval(prev_note) == 2 and prev_note.get_scale_degree_interval(note) != 2:
                            return False 
                        if note_before_prev.get_scale_degree_interval(prev_note) == -3 and next_note is not None and note.get_scale_degree_interval(next_note) != 2:
                            return False 
            if next_note is not None:
                if not self._is_valid_harmonically(cf_note, next_note):
                    if abs(note.get_scale_degree_interval(next_note)) != 2:
                        return False 
                    if note.get_scale_degree_interval(next_note) == 2 and note_after_next is not None and next_note.get_scale_degree_interval(note_after_next) != 2:
                        return False 
        return True 

    def _doesnt_create_parallels(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index 
        cf_note = self._cantus[bar]
        if beat == 3:
            next_note, cf_next_note = self._get_next_note(index), self._cantus[bar + 1]
            if next_note is None or abs(next_note.get_chromatic_interval(cf_next_note) % 12) not in [0, 7]:
                return True 
            upper_interval, lower_interval = note.get_scale_degree_interval(next_note), cf_note.get_scale_degree_interval(cf_next_note)
            if (upper_interval > 0 and lower_interval > 0) or (upper_interval < 0 and lower_interval < 0):
                return False
        if beat == 0:
            prev_note, cf_prev_note = self._get_prev_note(index), self._cantus[bar - 1]
            if prev_note is None or abs(note.get_chromatic_interval(cf_note) % 12) not in [0, 7]:
                return True 
            upper_interval, lower_interval = prev_note.get_scale_degree_interval(note), cf_prev_note.get_scale_degree_interval(cf_note)
            if (upper_interval > 0 and lower_interval > 0) or (upper_interval < 0 and lower_interval < 0):
                return False
        return True 

    def _no_large_parallel_leaps(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index 
        cf_prev, cf_note, cf_next = self._cantus[bar - 1], self._cantus[bar], self._cantus[bar + 1]
        if beat == 3:
            next_note = self._get_next_note(index)
            if next_note is not None:
                next_interval, cf_next_interval = note.get_scale_degree_interval(next_note), cf_note.get_scale_degree_interval(cf_next)
                if ((abs(next_interval) > 2 and abs(cf_next_interval) > 2 and (abs(next_interval) > 4 or abs(cf_next_interval) > 4) and 
                    ((next_interval > 0 and cf_next_interval > 0) or (next_interval < 0 and cf_next_interval < 0)))):
                    return False 
        if beat == 1:
            prev_note = self._get_prev_note(index) #this index will always exist when we check this 
            if prev_note is not None:
                prev_interval, cf_prev_interval = prev_note.get_scale_degree_interval(note), cf_prev.get_scale_degree_interval(cf_note)
                if ((abs(prev_interval) > 2 and abs(cf_prev_interval) > 2 and (abs(prev_interval) > 4 or abs(cf_prev_interval) > 4) and 
                    ((prev_interval > 0 and cf_prev_interval > 0) or (prev_interval < 0 and cf_prev_interval < 0)))):
                    return False 
        return True 

    def _no_cross_relations_with_cantus_firmus(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        cf_note = self._cantus[bar - 1 if beat == 0 else bar + 1]
        if beat not in [1, 2] and abs(cf_note.get_scale_degree_interval(note)) in [1, 8]:
            return cf_note.get_accidental() == note.get_accidental()
        return True 

    def _no_ascending_leaps_on_accented_beats(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index 
        if beat % 2 == 1 and self._get_prev_note(index) is not None:
            if self._get_prev_note(index).get_scale_degree_interval(note) > 2: return False 
        if beat % 2 == 0 and self._get_next_note(index) is not None:
            if note.get_scale_degree_interval(self._get_next_note(index)) > 2: return False 
        return True 

    def _current_chain_is_legal(self) -> bool:
        current_chain = []
        index = (0, 0) if self._start_on_beat else (0, 1)
        while index is not None and self._counterpoint[index] is not None:
            current_chain.append(self._counterpoint[index])
            index = self._get_next_index(index)
        result = self._span_is_valid(current_chain)
        return result

    def _span_is_valid(self, span: list[Note]) -> bool:
        if len(span) < 3: return True 
        check_ending = True if self._remaining_indices == 0 else False 
        if not self._segments_and_chains_are_legal(span, check_ending): return False 
        if not self._no_illegal_repetitions(span): return False 
        if not self._ascending_intervals_handled(span): return False 
        if not self._no_nearby_cross_relations(span): return False 
        return True 

    def _segments_and_chains_are_legal(self, span: list[Note], check_ending: bool) -> bool:
        intervals = [span[i - 1].get_scale_degree_interval(span[i]) for i in range(1, len(span))]
        for i in range(1, len(intervals)):
            if ((intervals[i - 1] > 0 and intervals[i] > 0) or (intervals[i - 1] < 0 and intervals[i] < 0)):
                if intervals[i] > intervals[i - 1] or abs(intervals[i - 1]) > 3 or abs(intervals[i]) > 3:
                    return False 

        span_indices_ending_segments = [0]
        for i in range(1, len(intervals)):
            if ((intervals[i - 1] > 0 and intervals[i] < 0) or (intervals[i - 1] < 0 and intervals[i] > 0)):
                span_indices_ending_segments.append(i)
        span_indices_ending_segments += [len(span) - 1] if check_ending else []
        for i in range(1, len(span_indices_ending_segments)):
            start_note, end_note = span[span_indices_ending_segments[i - 1]], span[span_indices_ending_segments[i]]
            if not self._is_valid_outline(start_note, end_note): return False 
        #next check leap chains
        chains = []
        prev_interval = None
        for i in range(len(intervals)):
            if abs(intervals[i]) > 2:
                if prev_interval is None or abs(prev_interval) <= 2:
                    chains.append([span[i], span[i + 1]])
                else:
                    chains[-1].append(span[i + 1])
            prev_interval = intervals[i]
        for chain in chains:
            for i in range(len(chain) - 2):
                for j in range(i + 2, len(chain)):
                    if not self._is_valid_outline(chain[i], chain[j]):
                        return False 
        return True 

    def _no_illegal_repetitions(self, span: list[Note]) -> bool:
        intervals = [span[i - 1].get_scale_degree_interval(span[i]) for i in range(1, len(span))]
        for i in range(len(span) - 2):
            (bar, beat) = self._all_indices[i]
            if beat != 3:
                if self._is_unison(span[i], span[i + 2]) and intervals[i] > 0:
                    return False 
            if beat == 0 and i < len(span) - 3:
                if intervals[i] == intervals[i + 2]:
                    return False 
                if i < len(span) - 6 and intervals[i] == intervals[i + 4] and intervals[i + 1] == intervals[i + 5]:
                    return False 
            if i < len(span) - 5 and intervals[i] == intervals[i + 3] and intervals[i + 1] == intervals[i + 4]:
                return False
            if i < len(span) - 5:
                repetitions = 0
                for j in range(i + 1, i + 6):
                    if self._is_unison(span[i], span[j]): repetitions += 1
                    if repetitions == 2: return False 
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
            elif span[i - 1].get_scale_degree_interval(span[i]) > 3 and span[i].get_scale_degree_interval(span[i + 1]) != -2:
                return False 
        return True 

    def _passes_final_checks(self, solution: list[Note]) -> bool:
        return self._leaps_filled_in(solution)

    def _leaps_filled_in(self, solution: list[Note]) -> bool:
        # print("running leaps filled in with solution:")
        # for n in solution: print(n)
        # for i in range(1, len(solution) - 1):
        #     interval = solution[i - 1].get_scale_degree_interval(solution[i])
        #     #for leaps down, we either need the note below the top note or any higher note 
        #     if interval < -2:
        #         handled = False 
        #         for j in range(i + 1, len(solution)):
        #             if solution[i - 1].get_scale_degree_interval(solution[j]) >= -2:
        #                 handled = True
        #                 break
        #         if not handled: 
        #             print("intervals not properly handled")
        #             return False 
        return True

    def _map_solution_onto_counterpoint_dict(self, solution: list[Note]) -> None:
        for i, note in enumerate(solution):
            (measure, beat) = self._all_indices[i]
            # if measure in self._divided_measures:
            #     note = Note(note.get_scale_degree(), note.get_octave(), 4, note.get_accidental())
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
        if ratio > .85: score += math.floor((ratio - .85) * 20)
        elif ratio < .85: score += math.floor((.85 - ratio) * 100)
        if num_leaps == 0: score += 15

        #next, find the frequency of the most repeated note
        most_frequent = 1
        for i, note in enumerate(solution):
            freq = 1
            for j in range(i + 1, len(solution)):
                if note.get_chromatic_interval(solution[j]) == 0:
                    freq += 1
            most_frequent = max(most_frequent, freq)
        max_acceptable = MaxAcceptableRepetitions[len(solution)]
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