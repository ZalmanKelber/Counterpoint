from random import random, shuffle, randint
import math
from time import time

from notation_system import ModeOption, ScaleOption, RangeOption, Note, ModeResolver 
from legal_intervals import LegalIntervalsFirstSpecies, MaxAcceptableRepetitions
from cantus_firmus import CantusFirmus, GenerateCantusFirmus

class GenerateMultiPartFirstSpecies:

    def __init__(self, length: int = None, height: int = 3, cf_index: int = 1, mode: ModeOption = None):
        self._height = height if height <= 6 else 6
        self._mode = mode or ModeOption.AEOLIAN
        self._length = length or 8 + math.floor(random() * 5) #todo: replace with normal distribution
        self._range = [RangeOption.BASS, RangeOption.TENOR, RangeOption.ALTO, RangeOption.SOPRANO] if height == 4 else [RangeOption.BASS, RangeOption.ALTO, RangeOption.SOPRANO]
        if height == 5:
            self._range = [RangeOption.BASS, RangeOption.TENOR, RangeOption.ALTO, RangeOption.SOPRANO, RangeOption.SOPRANO]
        if height == 6:
            self._range = [RangeOption.BASS, RangeOption.TENOR, RangeOption.TENOR, RangeOption.ALTO, RangeOption.SOPRANO, RangeOption.SOPRANO]
        self._mr = [ModeResolver(self._mode, range_option=self._range[i]) for i in range(self._height)]
        self._cf_index = cf_index
        self._melodic_insertion_checks = [
            self._handles_adjacents,
            self._handles_repetition,
            self._handles_repeated_two_notes,
            self._handles_repeated_three_note,
            self._handles_ascending_minor_sixth,
            self._handles_highest,
            self._handles_final_leading_tone,
            self._handles_final_note_in_top_voice,
            self._handles_sharp_notes,
            self._handles_large_leaps
        ]

        self._harmonic_insertion_checks = [
            self._handles_dissonance_with_bottom_voice,
            self._handles_dissonance_with_inner_voices,
            self._handles_hiddens_from_above,
            self._handles_hiddens_from_below,
            self._handles_parallels,
            self._handles_leaps_in_parallel_motion,
            self._handles_doubled_leading_tone,
            self._handles_first_note,
            self._handles_last_note,
            self._handles_three_voices_unison,
            self._handles_sixth_in_penultimate_bar
        ]

        self._index_checks = [
            self._highest_and_lowest_placed
        ]
        self._change_params = [
            self._check_for_highest_and_lowest,
        ]
        self._final_checks = [
            self._top_ends_by_step,
            self._augs_and_dims_resolved,
            self._no_closely_repeated_sonorities,
            self._check_last_top_note
        ]
        self._params = [
            "highest_has_been_placed", "lowest_has_been_placed",
        ]

    def print_counterpoint(self):
        print("        FIRST SPECIES WITH", self._height, "VOICES:")
        for i in range(self._length):
            row = "  "
            for line in range(self._height):
                note = str(self._counterpoint_obj[line][(i, 0)]) if self._counterpoint_obj[line][(i, 0)] is not None else ""
                row += note.ljust(25)
            print(row)
                
    def get_optimal(self):
        if len(self._solutions) == 0:
            return None 
        optimal = self._solutions[0]
        self._map_solution_onto_counterpoint_dict(optimal)
        self.print_counterpoint()
        return optimal

    def generate_mp1s(self, last_segment: bool = False):
        self._last_segment = last_segment
        print("MODE = ", self._mode.value["name"])
        self._solutions = []
        def attempt():
            self._num_backtracks = 0
            self._found_possible = False
            self._solutions_this_attempt = 0
            self._initialize()
            self._backtrack()
        attempts = 0
        while len(self._solutions) < 100 and attempts < 1:
            attempts += 1
            attempt()
        print("number of solutions:", len(self._solutions))
        if len(self._solutions) > 0:
            shuffle(self._solutions)
            self._solutions.sort(key = lambda sol: self._score_solution(sol)) 

    def _initialize(self) -> bool:
        indices = []
        for line in range(self._height):
            indices.append([])
            for bar in range(self._length - 1):
                for beat in [0]:
                    indices[line].append((bar, beat))
            indices[line].append((self._length - 1, 0))
        self._all_indices = [indices[line][:] for line in range(self._height)]
        self._remaining_indices = [indices[line][:] for line in range(self._height)]
        self._remaining_indices[self._cf_index] = []
        for line in range(self._height):
            self._remaining_indices[line].reverse()
        #initialize counterpoint data structure, that will map indices to notes
        self._counterpoint_obj = []
        for line in range(self._height): 
            self._counterpoint_obj.append({})
            for index in self._all_indices[line]:
                self._counterpoint_obj[line][index] = None 
        #also initialize counterpoint data structure as list 
        self._counterpoint_lst = []
        for line in range(self._height):
            self._counterpoint_lst.append([])
        #initialize parameters for this attempt
        self._attempt_params = []
        for line in range(self._height):
            self._attempt_params.append({})
        for line in range(self._height): self._attempt_params[line] = {
            "lowest": None, "highest": None, "highest_must_appear_by": None, "lowest_must_appear_by": None, 
            "highest_has_been_placed": False, "lowest_has_been_placed": False
        }
        self._store_params_stack = []
        for line in range(self._height):
            self._store_params_stack.append([])
        gcf = GenerateCantusFirmus(self._length, self._mode)
        cf = gcf.generate_cf(self._range[self._cf_index])
        while cf.get_notes()[-2].get_chromatic_interval(cf.get_notes()[-1]) == 2:
            cf = gcf.generate_cf(self._range[self._cf_index])
        self._counterpoint_lst[self._cf_index] = cf.get_notes()
        for bar, note in enumerate(self._counterpoint_lst[self._cf_index]):
            self._counterpoint_obj[self._cf_index][(bar, 0)] = note
        vocal_range = [] 
        for line in range(self._height):
            vocal_range.append(randint(6, 8))
        for line in range(self._height):
            if line != self._cf_index:
                self._attempt_params[line]["lowest"] = self._mr[line].get_default_note_from_interval(self._mr[line].get_lowest(), randint(1, 13 - vocal_range[line]))
                self._attempt_params[line]["highest"] = self._mr[line].get_default_note_from_interval(self._attempt_params[line]["lowest"], vocal_range[line])
                self._attempt_params[line]["highest_must_appear_by"] = randint(3, self._length - 1)
                self._attempt_params[line]["lowest_must_appear_by"] = randint(3 if self._attempt_params[line]["highest_must_appear_by"] >= 5 else 5, self._length - 1)

        self._valid_pitches = []
        for line in range(self._height):
            self._valid_pitches.append([])
        for line in range(self._height):
            if line != self._cf_index:
                valid_pitches = [self._attempt_params[line]["lowest"], self._attempt_params[line]["highest"]]
                for i in range(2, vocal_range[line]):
                    valid_pitches += self._mr[line].get_notes_from_interval(self._attempt_params[line]["lowest"], i)
                self._valid_pitches[line] = valid_pitches
        self._lowest_score = None

    def _backtrack(self) -> None:
        if self._solutions_this_attempt >= 10000 or self._num_backtracks > 50000 or (len(self._solutions) == 0 and self._num_backtracks > 5000):
            return 
        self._num_backtracks += 1
        if self._num_backtracks % 5000 == 0:
            print("num backtracks:", self._num_backtracks)
        if all([len(self._remaining_indices[line]) == 0 for line in range(self._height)]):
            if not self._found_possible:
                self._found_possible = True 
                print("found possible solution!  backtracks:", self._num_backtracks)
            if self._passes_final_checks():
                if self._solutions_this_attempt == 0:
                    print("FOUND SOLUTION!  backtracks:", self._num_backtracks)
                self._solutions.append([self._counterpoint_lst[line][:] for line in range(self._height)])
                self._solutions_this_attempt += 1
            return 
        line = 0
        while len(self._remaining_indices[line]) == 0:
            line += 1
        # if line != 0:
        #     print("made it to line", line)
        (bar, beat) = self._remaining_indices[line].pop() 
        if self._passes_index_checks((bar, beat), line):
            candidates = list(filter(lambda n: self._passes_insertion_checks(n, (bar, beat), line), self._valid_pitches[line]))
            shuffle(candidates)
            notes_to_insert = []
            for candidate in candidates: 
                durations = [8] if bar != self._length - 1 else [16]
                for dur in durations:
                    notes_to_insert.append(Note(candidate.get_scale_degree(), candidate.get_octave(), dur, accidental=candidate.get_accidental()))
            shuffle(notes_to_insert)
            for note_to_insert in notes_to_insert:
                self._insert_note(note_to_insert, (bar, beat), line)
                self._backtrack()
                self._remove_note(note_to_insert, (bar, beat), line)
        self._remaining_indices[line].append((bar, beat))

    def _passes_index_checks(self, index: tuple, line: int) -> bool:
        for check in self._index_checks:
            if not check(index, line): return False 
        return True

    def _passes_insertion_checks(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index 
        for check in self._melodic_insertion_checks:
            if not check(note, (bar, beat), line): 
                #print("failed insertion check:", str(note), index, "on function", check.__name__)
                return False 
        # print("passed insertion checks!", str(note), index)
        for check in self._harmonic_insertion_checks:
            if not check(note, (bar, beat), line): 
                #print("failed insertion check:", str(note), index, "on function", check.__name__)
                return False 
        return True 

    def _insert_note(self, note: Note, index: tuple, line: int) -> set:
        self._counterpoint_lst[line].append(note)
        self._counterpoint_obj[line][index] = note
        self._store_params_stack[line].append({})
        for param in self._params:
            self._store_params_stack[line][-1][param] = self._attempt_params[line][param]
        for check in self._change_params:
            check(note, index, line)

    def _remove_note(self, note: Note, index: tuple, line: int) -> set:
        self._counterpoint_lst[line].pop()
        self._counterpoint_obj[line][index] = None
        for param in self._params:
            self._attempt_params[line][param] = self._store_params_stack[line][-1][param]
        self._store_params_stack[line].pop()

    def _passes_final_checks(self) -> bool:
        for check in self._final_checks:
            if not check(): 
                # print("failed final check:", check.__name__)
                return False 
        return True 

    ######################################
    ### melodic insertion checks #########

    def _handles_adjacents(self, note: Note, index: tuple, line: int) -> bool:
        if index[0] == 0: return True 
        (sdg_interval, chro_interval) = self._mr[line].get_intervals(self._counterpoint_lst[line][-1], note)
        if sdg_interval not in LegalIntervalsFirstSpecies["adjacent_melodic_scalar"]: 
            return False 
        if chro_interval not in LegalIntervalsFirstSpecies["adjacent_melodic_chromatic"]: 
            return False 
        if (sdg_interval, chro_interval) in LegalIntervalsFirstSpecies["forbidden_combinations"]: 
            return False 
        return True 

    def _handles_ascending_minor_sixth(self, note: Note, index: tuple, line: int) -> bool:
        if len(self._counterpoint_lst[line]) < 2: return True 
        if self._counterpoint_lst[line][-2].get_chromatic_interval(self._counterpoint_lst[line][-1]) == 8:
            return self._counterpoint_lst[line][-1].get_chromatic_interval(note) == -1
        return True

    def _handles_repetition(self, note: Note, index: tuple, line: int) -> bool:
        if line == 0 and index[0] != 0 and self._counterpoint_lst[line][-1].get_scale_degree() == note.get_scale_degree(): 
            return False 
        if len(self._counterpoint_lst[line]) < 2: return True
        if self._mr[line].is_unison(self._counterpoint_lst[line][-1], note) and self._mr[line].is_unison(self._counterpoint_lst[line][-2], self._counterpoint_lst[line][-1]):
            return False 
        return True 

    def _handles_repeated_two_notes(self, note: Note, index: tuple, line: int) -> bool:
        if index[0] < 3: return True 
        if self._mr[line].is_unison(self._counterpoint_lst[line][-3], self._counterpoint_lst[line][-1]) and self._mr[line].is_unison(self._counterpoint_lst[line][-2], note):
            return False 
        return True 

    def _handles_repeated_three_note(self, note: Note, index: tuple, line: int) -> bool:
        if index[0] < 5: return True 
        for i in range(index[0] - 4):
            if (self._mr[line].is_unison(self._counterpoint_lst[line][i], self._counterpoint_lst[line][-2]) and 
                self._mr[line].is_unison(self._counterpoint_lst[line][i + 1], self._counterpoint_lst[line][-1]) and 
                self._mr[line].is_unison(self._counterpoint_lst[line][i + 2], note)):
                return False 
        return True 

    def _handles_highest(self, note: Note, index: tuple, line: int) -> bool:
        if self._attempt_params[line]["highest_has_been_placed"] and self._mr[line].is_unison(self._attempt_params[line]["highest"], note):
            return False 
        return True 

    def _handles_final_leading_tone(self, note: Note, index: tuple, line: int) -> bool:
        if index != (self._length - 2, 0): return True 
        final = self._mr[line].get_final() 
        if line != 0 and self._counterpoint_lst[0][self._length - 1].get_scale_degree() != final: return True 
        if (note.get_scale_degree() + 1) % 7 != final: return True 
        if (final in [2, 5, 6] and note.get_accidental() != ScaleOption.SHARP) or (final in [1, 3, 4] and note.get_accidental() != ScaleOption.NATURAL):
            return False 
        if final == 3 and note.get_scale_degree() == 4 and note.get_accidental() == ScaleOption.SHARP:
            return False
        return True 

    def _handles_final_note_in_top_voice(self, note: Note, index: tuple, line: int) -> bool:
        if index != (self._length - 1, 0) or line != self._height - 1: return True 
        if abs(self._counterpoint_lst[line][-1].get_scale_degree_interval(note)) > 2: return False 
        return True 

    def _handles_sharp_notes(self, note: Note, index: tuple, line: int) -> bool:
        if index[0] == 0: return True 
        prev_note = self._counterpoint_lst[line][-1]
        if self._mr[line].is_sharp(prev_note) and prev_note.get_scale_degree_interval(note) != 2:
            return False 
        return True

    def _handles_large_leaps(self, note: Note, index: tuple, line: int) -> bool:
        if index[0] < 2: return True 
        prev_intvl = self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1])
        intvl = self._counterpoint_lst[line][-1].get_scale_degree_interval(note)
        if prev_intvl > 0 and intvl > 4: return False 
        if prev_intvl < -4 and intvl < 0: return False 
        return True

    ######################################
    ###### harmonic insertion checks ######

    def _handles_dissonance_with_bottom_voice(self, note: Note, index: tuple, line: int) -> bool:
        (low_note, high_note) = (self._counterpoint_obj[0][index], note) if line != 0 else (note, self._counterpoint_obj[self._cf_index][index])
        if self._mr[line].is_sharp(low_note) and self._mr[line].is_sharp(high_note): return False 
        (sdg_interval, chro_interval) = self._mr[line].get_intervals(low_note, high_note)
        if chro_interval < 0: return False 
        if sdg_interval % 7 not in [1, 3, 5, 6]: return False 
        if chro_interval % 12 not in [0, 3, 4, 7, 8, 9]: return False 
        if sdg_interval % 7 == 5 and chro_interval % 12 == 8: return False 
        return True 

    def _handles_dissonance_with_inner_voices(self, note: Note, index: tuple, line: int) -> bool:
        if line == 0: return True 
        for other_line in range(1, self._height):
            if other_line < line or other_line == self._cf_index:
                if self._mr[line].is_sharp(note) and self._mr[line].is_sharp(self._counterpoint_obj[other_line][index]): return False
                (sdg_interval, chro_interval) = self._mr[line].get_intervals(note, self._counterpoint_obj[other_line][index])
                if abs(line - other_line) == 1 and abs(chro_interval) > 12: return False 
                if abs(sdg_interval) % 7 not in [1, 3, 4, 5, 6]: return False 
                if abs(chro_interval) % 12 in [1, 2, 10, 11]: return False 
        return True 

    def _handles_hiddens_from_above(self, note: Note, index: tuple, line: int) -> bool:
        bar = index[0]
        if bar == 0 or line != self._height - 1 or abs(self._counterpoint_lst[line][-1].get_scale_degree_interval(note)) <= 2: return True 
        if abs(self._counterpoint_obj[0][index].get_chromatic_interval(note)) % 12 not in [0, 7]: return True 
        upper, lower = self._counterpoint_lst[line][-1].get_scale_degree_interval(note), self._counterpoint_obj[0][(bar - 1, 0)].get_scale_degree_interval(self._counterpoint_obj[0][index])
        if (upper > 0 and lower > 0) or (upper < 0 and lower < 0): return False 
        return True 

    def _handles_hiddens_from_below(self, note: Note, index: tuple, line: int) -> bool:
        bar = index[0]
        if bar == 0 or self._cf_index != self._height - 1 or line != 0: return True 
        if abs(self._counterpoint_obj[self._height - 1][(bar - 1, 0)].get_scale_degree_interval(self._counterpoint_obj[self._height - 1][index])) <= 2: return True 
        if abs(self._counterpoint_obj[self._height - 1][index].get_chromatic_interval(note)) % 12 not in [0, 7]: return True 
        upper, lower = self._counterpoint_obj[self._height - 1][(bar - 1, 0)].get_scale_degree_interval(self._counterpoint_obj[self._height - 1][index]), self._counterpoint_obj[0][(bar - 1, 0)].get_scale_degree_interval(note)
        if (upper > 0 and lower > 0) or (upper < 0 and lower < 0): return False 
        return True 

    def _handles_parallels(self, note: Note, index: tuple, line: int) -> bool:
        bar = index[0]
        if bar == 0: return True 
        for other_line in range(self._height):
            if other_line >= line and other_line != self._cf_index: break
            intvl = self._counterpoint_obj[other_line][index].get_scale_degree_interval(note)
            if abs(intvl) % 7 in [1, 5] and self._counterpoint_obj[other_line][(bar - 1, 0)].get_scale_degree_interval(self._counterpoint_obj[line][(bar - 1, 0)]) == intvl:
                return False 
        return True 

    def _handles_leaps_in_parallel_motion(self, note: Note, index: tuple, line: int) -> bool:
        bar = index[0]
        if (line != self._height - 1 and self._cf_index != self._height - 1) or line != self._height - 2 or bar == 0: return True
        intervals = [self._counterpoint_obj[other_line][(bar - 1, 0)].get_scale_degree_interval(self._counterpoint_obj[other_line][index] if other_line != line else note) for other_line in range(self._height)] 
        if not all([intvl > 0 for intvl in intervals]) and not all([intvl < 0 for intvl in intervals]): return True 
        for intvl in intervals:
            if abs(intvl) >= 4: return False 
        return True 

    def _handles_doubled_leading_tone(self, note: Note, index: tuple, line: int) -> bool:
        if not self._mr[line].should_not_be_doubled(note): return True 
        for other_line in range(self._height):
            if other_line >= line and other_line != self._cf_index: return True 
            if abs(self._counterpoint_obj[other_line][index].get_chromatic_interval(note)) % 12 == 0: return False 
        return True

    def _handles_first_note(self, note: Note, index: tuple, line: int) -> bool:
        if index[0] != 0: return True 
        intvl = self._counterpoint_obj[0][(0, 0)].get_chromatic_interval(note) if line != 0 else note.get_chromatic_interval(self._counterpoint_obj[self._cf_index][(0, 0)])
        if intvl < 0 or intvl % 12 not in [0, 4, 7]: return False 
        if line != self._height - 1 and (line != self._height - 2 or self._cf_index != self._height - 1): return True 
        has_fifth, has_third = False, False 
        for i in range(1, self._height):
            low_note, high_note = self._counterpoint_obj[0][(0, 0)], self._counterpoint_obj[i][(0, 0)]
            if low_note is None or high_note is None: break
            intvl_to_check = low_note.get_chromatic_interval(high_note) % 12 
            if intvl_to_check == 4: has_third = True 
            if intvl_to_check == 7: has_fifth = True 
        if not has_third or not has_fifth: return False 
        return True 

    def _handles_last_note(self, note: Note, index: tuple, line: int) -> bool:
        if index[0] != self._length - 1: return True 
        if line == 0: return note.get_scale_degree() == self._mr[line].get_final()
        intvl = self._counterpoint_obj[0][(self._length - 1, 0)].get_chromatic_interval(note) 
        if intvl < 0 or intvl % 12 not in [0, 4, 7]: return False 
        if self._height >= 4 and (line == self._height - 1 or (line == self._height - 2 and self._cf_index == self._height - 1)):
            has_third = False 
            bass_note = self._counterpoint_obj[0][index]
            for other_line in range(1, self._height):
                if other_line != line and bass_note.get_chromatic_interval(self._counterpoint_obj[other_line][index]) % 12 == 4:
                    has_third = True 
            if not has_third and bass_note.get_chromatic_interval(note) % 12 != 4: return False
        return True 

    def _handles_three_voices_unison(self, note: Note, index: tuple, line: int) -> bool:
        if index[0] in [0, self._length - 1]: return True 
        num_unisons = 0
        for other_line in range(self._height):
            if other_line < line or other_line == self._cf_index:
                if self._mr[line].is_unison(note, self._counterpoint_obj[other_line][index]):
                    num_unisons += 1
        return num_unisons < 2

    def _handles_sixth_in_penultimate_bar(self, note: Note, index: tuple, line: int) -> bool:
        if index[0] != self._length - 2: return True 
        low_note = note if line == 0 else self._counterpoint_obj[0][index]
        high_note = self._counterpoint_obj[self._cf_index][index] if line == 0 else note 
        final = self._mr[line].get_final()
        intvl = low_note.get_scale_degree_interval(high_note) % 7
        if intvl == 6:
            if self._mr[line].get_default_note_from_interval(low_note, -2).get_scale_degree() != final: return False 
            for line_to_check in range(1, self._height):
                note_to_check = self._counterpoint_obj[line_to_check][index]
                if note_to_check is not None and low_note.get_chromatic_interval(note_to_check) % 12 == 4:
                    return False
        if intvl == 5:
            if ( self._mr[line].get_default_note_from_interval(low_note, -4).get_scale_degree() != final and 
                self._mr[line].get_default_note_from_interval(low_note, -5).get_scale_degree() != final): return False 
            return True 
        return True 



    ##########################################
    ########### index checks #################

    def _highest_and_lowest_placed(self, index: tuple, line: int) -> bool:
        (bar, beat) = index 
        if bar >= self._attempt_params[line]["highest_must_appear_by"] and not self._attempt_params[line]["highest_has_been_placed"]:
            return False 
        if bar >= self._attempt_params[line]["lowest_must_appear_by"] and not self._attempt_params[line]["lowest_has_been_placed"]:
            return False 
        return True 

    ##########################################
    ########### insert functions #############


    def _check_for_highest_and_lowest(self, note: Note, index: tuple, line: int) -> None:
        if self._mr[line].is_unison(note, self._attempt_params[line]["highest"]):
            self._attempt_params[line]["highest_has_been_placed"] = True 
        if self._mr[line].is_unison(note, self._attempt_params[line]["lowest"]):
            self._attempt_params[line]["lowest_has_been_placed"] = True 

    ##########################################
    ########### final checks #################

    def _top_ends_by_step(self) -> bool:
        for line in range(1, self._height - 1):
            if ( self._counterpoint_lst[line][-1].get_chromatic_interval(self._counterpoint_lst[self._height - 1][-1]) < 0 or 
                self._counterpoint_lst[line][-2].get_chromatic_interval(self._counterpoint_lst[self._height - 1][-2]) < 0 ):
                if abs(self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1])) > 2: return False 
        return True 

    def _augs_and_dims_resolved(self) -> bool:
        for i in range(1, self._length - 1):
            minor_third_lines, major_third_lines, minor_sixth_lines, major_sixth_lines = [], [], [], []
            for line in range(1, self._height):
                intvl = self._counterpoint_lst[0][i].get_chromatic_interval(self._counterpoint_lst[line][i]) % 12
                if intvl == 3: minor_third_lines.append(line)
                if intvl == 4: major_third_lines.append(line)
                if intvl == 8: minor_sixth_lines.append(line)
                if intvl == 9: major_sixth_lines.append(line)
            if len(minor_third_lines) > 0 and len(major_sixth_lines) > 0:
                if len(major_sixth_lines) > 1: return False 
                if self._counterpoint_lst[major_sixth_lines[0]][i].get_scale_degree_interval(self._counterpoint_lst[major_sixth_lines[0]][i + 1]) != 2:
                    return False 
                if self._counterpoint_lst[0][i].get_chromatic_interval(self._counterpoint_lst[0][i + 1]) != -2:
                    return False 
            if len(major_third_lines) > 0 and len(minor_sixth_lines) > 0:
                if len(major_third_lines) > 1: return False 
                if self._counterpoint_lst[major_third_lines[0]][i].get_chromatic_interval(self._counterpoint_lst[major_third_lines[0]][i + 1]) != 1:
                    return False 
                if self._counterpoint_lst[0][i].get_chromatic_interval(self._counterpoint_lst[0][i + 1]) != 1:
                    return False 
                for line_to_resolve in minor_sixth_lines:
                    if self._counterpoint_lst[line_to_resolve][i].get_chromatic_interval(self._counterpoint_lst[line_to_resolve][i + 1]) != 0:
                        return False
        return True

    def _no_closely_repeated_sonorities(self) -> bool:
        for i in range(self._height - 2):
            if all([self._mr[line].is_unison(self._counterpoint_lst[line][i], self._counterpoint_lst[line][i + 2]) for line in range(self._height)]):
                return False 
        return True 

    def _check_last_top_note(self) -> bool:
        if not self._last_segment: return True 
        highest, highest_note = 0, None
        for line in range(1, self._height):
            note = self._counterpoint_obj[line][(self._length - 1, 0)]
            if note.get_chromatic_with_octave() > highest:
                highest = note.get_chromatic_with_octave()
                highest_note = note 
        if highest_note.get_scale_degree() != self._mr[line].get_final(): return False 
        return True
    

    ##########################################
    ########### scoring ######################

    def _score_solution(self, solution: list[list[Note]]) -> int:
        score = 0
        self._map_solution_onto_counterpoint_dict(solution)
        for i in range(self._length):
            has_third, has_fifth_or_sixth = False, False
            for line in range(1, self._height):
                intvl = self._counterpoint_lst[0][i].get_scale_degree_interval(self._counterpoint_lst[line][i])
                if intvl % 7 == 3: has_third = True 
                if intvl % 7 in [5, 6]: has_fifth_or_sixth = True 
            if not has_third or not has_fifth_or_sixth: score += 100
                
        for line in range(1, self._height):
            num_steps = 0
            for i in range(1, self._length - 1):
                if abs(self._counterpoint_lst[line][i - 1].get_scale_degree_interval(self._counterpoint_lst[line][i])) == 2:
                    num_steps += 1
            steps_ratio = num_steps / (self._length - 1)
            IDEAL_STEPS = .712
            if steps_ratio <= IDEAL_STEPS: score += math.floor((IDEAL_STEPS - steps_ratio) * 100)
        return score 

    def _map_solution_onto_counterpoint_dict(self, solution: list[list[Note]]) -> None:
        for line in range(self._height):
            self._counterpoint_obj[line] = {}
            self._counterpoint_lst[line] = []
            self._all_indices[line] = []
            bar, beat = 0, 0
            for note in solution[line]:
                self._counterpoint_obj[line][(bar, beat)] = note
                self._counterpoint_lst[line].append(note)
                self._all_indices[line].append((bar, beat))
                bar += 1
