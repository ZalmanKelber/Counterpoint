import sys

from random import random, shuffle, randint
import math
from time import time

from notation_system import ModeOption, ScaleOption, Note, ModeResolver 
from cantus_firmus import CantusFirmus, GenerateCantusFirmus
from two_part_first_species import Orientation
from legal_intervals import LegalIntervalsFourthSpecies, MaxAcceptableRepetitions

class GenerateTwoPartFourthSpecies:

    def __init__(self, length: int = None, mode: ModeOption = None, octave: int = 4, orientation: Orientation = Orientation.ABOVE):
        self._orientation = orientation
        self._mode = mode or ModeOption.DORIAN
        self._length = length or 8 + math.floor(random() * 5) #todo: replace with normal distribution
        self._octave = octave
        self._mr = ModeResolver(self._mode)
        gcf = GenerateCantusFirmus(self._length, self._mode, self._octave)
        cf = None 
        #if the Cantus Firmus doesn't generate, we have to try again
        #also, for anything above the first species, the Cantus Firmus must end stepwise
        while cf is None or abs(cf.get_note(self._length - 2).get_scale_degree_interval(cf.get_note(self._length - 1))) > 2:
            cf = gcf.generate_cf()
        self._cantus_object = cf
        self._cantus = cf.get_notes()

    def print_counterpoint(self):
        print("  CANTUS FIRMUS:       COUNTERPOINT:")
        for i in range(self._length):
            for j in [0, 2]:
                cntpt_note = self._counterpoint[(i, j)] if (i, j) in self._counterpoint else ""
                if j == 0:
                    print("  " + str(self._cantus[i]) + "  " + str(cntpt_note))
                else:
                    print("                       " + str(cntpt_note))

    def get_optimal(self):
        if len(self._solutions) == 0:
            return None 
        optimal = self._solutions[0]
        print("optimal solution")
        for n in optimal: print(n)
        self._map_solution_onto_counterpoint_dict(optimal)
        self.print_counterpoint()
        return [optimal, self._cantus]
            
    def generate_2p4s(self):
        start_time = time()
        print("MODE = ", self._mode.value["name"])
        self._solutions = []
        def attempt():
            self._num_backtracks = 0
            self._solutions_this_attempt = 0
            initialized = self._initialize()
            while not initialized:
                initialized = self._initialize()
            self._backtrack()
        attempts = 0
        attempt()
        while len(self._solutions) < 1 and attempts < 20:
            print("attempt", attempts)
            attempt()
            attempts += 1
        print("number of attempts:", attempts)
        print("number of solutions:", len(self._solutions))
        if len(self._solutions) > 0:
            self._solutions.sort(key = lambda sol: self._score_solution(sol)) 

    def _initialize(self) -> bool:
        indices = []
        for i in range(self._length - 1):
            indices += [(i, 0), (i, 2)]
        indices += [(self._length - 1, 0)]
        self._all_indices = indices[:]
        self._remaining_indices = indices[:]
        self._remaining_indices.reverse()
        #initialize counterpoint data structure, that will map indices to notes
        counterpoint = {}
        for index in self._all_indices: counterpoint[index] = None 
        self._counterpoint = counterpoint
        last_note = self._mr.get_default_note_from_interval(self._cantus[self._length - 1], [-8, 1, 8][randint(0, 2)])
        vocal_range = randint(5, 8)
        highest = self._mr.get_default_note_from_interval(last_note, randint(2, vocal_range))
        lowest = self._mr.get_default_note_from_interval(highest, vocal_range * -1)
        valid_pitches = [lowest, highest] #order is unimportant
        for i in range(2, vocal_range):
            valid_pitches += self._mr.get_notes_from_interval(lowest, i)
        self._highest, self._lowest, self._last_note = highest, lowest, last_note
        self._highest_must_appear_by = randint(2, self._length - 2)
        self._lowest_must_appear_by = randint(2 if self._highest_must_appear_by >= 4 else 4, self._length - 1)
        self._valid_pitches = valid_pitches
        self._highest_has_been_placed = False 
        self._lowest_has_been_placed = False 
        return True 

    def _backtrack(self) -> None:
        if self._num_backtracks > 2000 and self._solutions_this_attempt == 0:
            return 
        if self._solutions_this_attempt >= 100:
            return 
        self._num_backtracks += 1
        if len(self._remaining_indices) == 0:
            # print("found possible solution!")
            sol = []
            for i in range(len(self._all_indices)):
                note_to_add = self._counterpoint[self._all_indices[i]]
                note_to_add_copy = Note(note_to_add.get_scale_degree(), note_to_add.get_octave(), note_to_add.get_duration(), note_to_add.get_accidental())
                sol.append(note_to_add_copy)
            if self._passes_final_checks(sol):
                # print("FOUND SOLUTION!")
                self._solutions.append(sol)
                self._solutions_this_attempt += 1
            return 
        (bar, beat) = self._remaining_indices.pop() 
        candidates = None
        if bar == self._length - 1:
            candidates = [self._last_note] if self._passes_insertion_checks(self._last_note, (bar, beat)) else []
        elif bar == 0 and (beat == 0 or self._counterpoint[(0, 0)].get_accidental == ScaleOption.REST):
            candidates = list(filter(lambda n: n.get_chromatic_interval(self._cantus[0]) in [-12, 0, 7, 12], self._valid_pitches))
        else:
            candidates = list(filter(lambda n: self._passes_insertion_checks(n, (bar, beat)), self._valid_pitches)) 
        if bar == 0 and beat == 0:
            candidates.append(Note(1, 0, 4, accidental = ScaleOption.REST))
        for candidate in candidates:
            #start by making a copy of the note
            candidate = Note(candidate.get_scale_degree(), candidate.get_octave(), 8, candidate.get_accidental())
            temp_highest_placed, temp_lowest_placed = self._highest_has_been_placed, self._lowest_has_been_placed
            if self._mr.is_unison(candidate, self._highest): self._highest_has_been_placed = True  
            if self._mr.is_unison(candidate, self._lowest): self._lowest_has_been_placed = True 
            (may_be_tied, must_be_tied) = self._get_tied_options(candidate, (bar, beat))
            if not must_be_tied:
                candidate.set_duration(4 if bar != self._length - 1 else 16)
                self._counterpoint[(bar, beat)] = candidate 
                if self._current_chain_is_legal((bar, beat)):
                    self._backtrack()
            if may_be_tied or (bar == self._length - 2 and beat == 0):
                candidate.set_duration(8)
                index_to_remove = (bar, 2) if beat == 0 else (bar + 1, 0)
                index_position_all, index_position_remaining = self._all_indices.index(index_to_remove), self._remaining_indices.index(index_to_remove)
                self._all_indices.remove(index_to_remove)
                self._remaining_indices.remove(index_to_remove)
                del self._counterpoint[index_to_remove]
                self._counterpoint[(bar, beat)] = candidate 
                if self._current_chain_is_legal((bar, beat)):
                    self._backtrack()
                self._all_indices.insert(index_position_all, index_to_remove)
                self._remaining_indices.insert(index_position_remaining, index_to_remove)
                self._counterpoint[index_to_remove] = None 
            self._highest_has_been_placed, self._lowest_has_been_placed = temp_highest_placed, temp_lowest_placed
        self._counterpoint[(bar, beat)] = None 
        self._remaining_indices.append((bar, beat))

    def _passes_insertion_checks(self, note: Note, index: tuple) -> bool:
        if not self._is_valid_melodic_insertion(note, index): return False #checks for properly resolved ascending sixths and non-adjacent cross relations 
        if not self._valid_harmonic_insertion(note, index): return False #makes sure all dissonances are resolved
        if not self._doesnt_create_parallels(note, index): return False #eliminates parallels and hidden fifths
        if not self._no_large_parallel_leaps(note, index): return False 
        if not self._no_cross_relations_with_cantus_firmus(note, index): return False 
        if not self._handles_highest_and_lowest(note, index): return False 
        return True 

    def _is_valid_melodic_insertion(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        prev_note = self._get_prev_note(index)
        if not self._is_valid_adjacent(prev_note, note): return False 
        #check to make sure an ascending minor sixth is handled 
        note_before_prev = self._get_prev_note(self._get_prev_index(index))
        if note_before_prev is not None and note_before_prev.get_accidental() == ScaleOption.REST: note_before_prev = None
        if note_before_prev is not None and note_before_prev.get_chromatic_interval(prev_note) == 8 and prev_note.get_chromatic_interval(note) != -1:
            return False
        if note_before_prev is not None and note_before_prev.get_scale_degree_interval(note) == 1 and note_before_prev.get_chromatic_interval(note) != 0:
            return False
        if bar == self._length - 1 and abs(prev_note.get_scale_degree_interval(note)) != 2: return False
        if bar == self._length - 1 and prev_note.get_scale_degree_interval(note) == 2 and not self._mr.is_unison(prev_note, self._mr.get_leading_tone_of_note(self._last_note)): return False
        return True 

    def _valid_harmonic_insertion(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        #case 1: beat == 0 -> test for dissonance in previous measure 
        #case 2: if previous note is tied: if dissonant, resolve it.  If not, see if it is consonant or a passing tone 
        if beat == 0:
            if not self._is_valid_harmonically(note, self._cantus[bar]): return False 
            if bar != 0 and not self._is_valid_harmonically(self._get_prev_note(index), self._cantus[bar - 1]):
                prev_note = self._get_prev_note(index)
                if self._counterpoint[(bar - 1, 0)].get_scale_degree_interval(prev_note) != prev_note.get_scale_degree_interval(note):
                    return False 
            return True 
        elif (bar, 0) in self._counterpoint:
            if self._is_valid_harmonically(note, self._cantus[bar]): return True 
            if abs(self._get_prev_note(index).get_scale_degree_interval(note)) != 2: return False 
            return True 
        else:
            if not self._is_valid_harmonically(self._get_prev_note(index), self._cantus[bar]) and self._get_prev_note(index).get_scale_degree_interval(note) != -2:
                return False 
            if not self._is_valid_harmonically(self._cantus[bar], note): return False 
            return True 

    def _doesnt_create_parallels(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index 
        if beat != 0 or bar == 0: return True 
        if self._cantus[bar].get_chromatic_interval(note) not in [-19, -12, -7, 0, 7, 12, 19]: return True 
        lower_interval, higher_interval = self._cantus[bar - 1].get_scale_degree_interval(self._cantus[bar]), self._get_prev_note(index).get_scale_degree_interval(note)
        if (lower_interval > 0 and higher_interval > 0) or (lower_interval < 0 and higher_interval < 0):
            return False 
        return True 

    def _no_large_parallel_leaps(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index 
        if beat == 2 or (bar - 1, 2) not in self._counterpoint: return True 
        lower_interval, higher_interval = self._cantus[bar - 1].get_scale_degree_interval(self._cantus[bar]), self._get_prev_note(index).get_scale_degree_interval(note)
        if abs(lower_interval > 2) and abs(higher_interval) > 2 and (abs(lower_interval) > 4 or abs(higher_interval) > 4) and ((lower_interval > 0 and higher_interval > 0) or (lower_interval < 0) and higher_interval < 0):
            return False 
        return True 

    def _no_cross_relations_with_cantus_firmus(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if bar > 0 and beat == 0 and self._cantus[bar - 1].get_scale_degree_interval(note) in [-8, 1, 8] and self._cantus[bar - 1].get_chromatic_interval(note) not in [-12, 0, 12]:
            return False 
        if beat == 2 and self._cantus[bar + 1].get_scale_degree_interval(note) in [-8, 1, 8] and self._cantus[bar + 1].get_chromatic_interval(note) not in [-12, 0, 12]:
            return False 
        return True 

    def _handles_highest_and_lowest(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index 
        if self._highest_must_appear_by == bar and not self._highest_has_been_placed and not self._mr.is_unison(self._highest, note): return False 
        if self._highest_has_been_placed and self._mr.is_unison(note, self._highest): return False 
        if self._lowest_must_appear_by == bar and not self._lowest_has_been_placed and not self._mr.is_unison(self._lowest, note): return False 
        return True 

    def _get_tied_options(self, note: Note, index: tuple) -> tuple:
        (bar, beat) = index 
        if bar >= self._length - 2 or beat == 0 or not self._is_valid_harmonically(self._cantus[bar], note): return (False, False)
        (may_be_tied, must_be_tied) = (False, False)
        next_harmonic_interval = self._cantus[bar + 1].get_scale_degree_interval(note)
        if next_harmonic_interval in [-9, -2, 4, 7, 11] or (next_harmonic_interval == -5 and self._cantus[bar + 1].get_chromatic_interval(note) == -8):
            may_be_tied, must_be_tied = True, True
        elif self._is_valid_harmonically(self._cantus[bar + 1], note):
            may_be_tied = True 
        return (may_be_tied, must_be_tied)

    def _current_chain_is_legal(self, index: tuple) -> bool:
        current_chain = []
        for i in range(self._all_indices.index(index) + 1):
            next_note = self._counterpoint[self._all_indices[i]]
            if next_note.get_accidental() != ScaleOption.REST:
                current_chain.append(next_note)
        result = self._span_is_valid(current_chain)
        return result

    def _span_is_valid(self, span: list[Note]) -> bool:
        if len(span) < 3: return True 
        last_second_species_chain = []
        search_index = len(span) - 1 if span[-1].get_duration() == 4 else len(span) - 2
        while search_index >= 0 and span[search_index].get_duration() == 4:
            last_second_species_chain.append(span[search_index])
            search_index -= 1
        if len(last_second_species_chain) < 3: return True 
        last_second_species_chain.reverse()
        intervals = []
        for i in range(len(last_second_species_chain) - 1):
            intervals.append(last_second_species_chain[i].get_scale_degree_interval(last_second_species_chain[i + 1]))
        for i, interval in enumerate(intervals):
            if interval >= 4:
                for j in range(i - 1, -1, -1):
                    if intervals[j] < 0: break 
                    if intervals[j] > 2: return False 
            if interval <= -4:
                for j in range(i + 1, len(intervals)):
                    if intervals[j] > 0: break
                    if intervals[j] < -2: return False 
        return True 

    def _passes_final_checks(self, solution: list[Note]) -> bool:
        if len(solution) >= self._length * 1.4: return False
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
        self._counterpoint = {}
        bar, beat = 0, 0
        self._all_indices = []
        for note in solution:
            self._counterpoint[(bar, beat)] = note
            self._all_indices.append((bar, beat))
            beat += note.get_duration() / 2 
            while beat >= 4:
                beat -= 4
                bar += 1

    def _score_solution(self, solution: list[Note]) -> int:
        return len(solution)

    def _is_valid_adjacent(self, note1: Note, note2: Note) -> bool:
        sdg_interval = note1.get_scale_degree_interval(note2)
        chro_interval = note1.get_chromatic_interval(note2)
        if ( sdg_interval in LegalIntervalsFourthSpecies["adjacent_melodic_scalar"] 
            and chro_interval in LegalIntervalsFourthSpecies["adjacent_melodic_chromatic"]
            and (sdg_interval, chro_interval) not in LegalIntervalsFourthSpecies["forbidden_combinations"] ):
            return True 
        return False 

    def _is_valid_outline(self, note1: Note, note2: Note) -> bool:
        sdg_interval = note1.get_scale_degree_interval(note2)
        chro_interval = note1.get_chromatic_interval(note2)
        if ( sdg_interval in LegalIntervalsFourthSpecies["outline_melodic_scalar"] 
            and chro_interval in LegalIntervalsFourthSpecies["outline_melodic_chromatic"]
            and (sdg_interval, chro_interval) not in LegalIntervalsFourthSpecies["forbidden_combinations"] ):
            return True 
        return False 

    def _is_valid_harmonically(self, note1: Note, note2: Note) -> bool:
        sdg_interval = note1.get_scale_degree_interval(note2)
        chro_interval = note1.get_chromatic_interval(note2)
        if ( sdg_interval in LegalIntervalsFourthSpecies["harmonic_scalar"] 
            and chro_interval in LegalIntervalsFourthSpecies["harmonic_chromatic"]
            and (sdg_interval, chro_interval) not in LegalIntervalsFourthSpecies["forbidden_combinations"] ):
            return True 
        return False 

    def _get_prev_note(self, index: tuple) -> Note:
        prev_index = self._get_prev_index(index)
        return None if prev_index is None else self._counterpoint[prev_index]

    def _get_next_note(self, index: tuple) -> Note:
        next_index = self._get_next_index(index)
        return None if next_index is None else self._counterpoint[next_index]

    def _get_prev_index(self, index: tuple) -> tuple:
        if index is None: return None
        i = self._all_indices.index(index)
        if i == 0: return None
        return self._all_indices[i - 1]

    def _get_next_index(self, index: tuple) -> tuple:
        i = self._all_indices.index(index)
        if i == len(self._all_indices) - 1: return None 
        return self._all_indices[i + 1]