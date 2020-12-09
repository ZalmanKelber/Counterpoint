from random import random, shuffle, randint
import math
from time import time

from notation_system import ModeOption, ScaleOption, RangeOption, Note, ModeResolver 
from two_part_first_species import Orientation
from legal_intervals import LegalIntervalsFifthSpecies, MaxAcceptableRepetitions

class GenerateTwoPartFreeCounterpoint:

    def __init__(self, length: int = None, mode: ModeOption = None,):
        self._mode = mode or ModeOption.AEOLIAN
        self._length = length or 8 + math.floor(random() * 5) #todo: replace with normal distribution
        self._range = [RangeOption.TENOR, RangeOption.ALTO]
        self._mr = [ModeResolver(self._mode, range_option=self._range[0]), ModeResolver(self._mode, range_option=self._range[1])]
        self._melodic_insertion_checks = [
            self._handles_adjacents,
            self._handles_interval_order,
            self._handles_nearby_augs_and_dims,
            self._handles_nearby_leading_tones,
            self._handles_ascending_minor_sixth,
            self._handles_ascending_quarter_leaps,
            self._handles_descending_quarter_leaps,
            self._handles_repetition,
            self._handles_eigths,
            self._handles_highest,
            self._handles_resolution_of_anticipation,
            self._handles_repeated_two_notes,
            self._handles_quarter_between_two_leaps,
            self._handles_upper_neighbor,
            self._handles_antipenultimate_bar,
        ]
        # self._harmonic_insertion_checks = [
        #     self._filters_dissonance_on_downbeat,
        #     self._resolves_suspension,
        #     self._prepares_weak_quarter_dissonance,
        #     self._resolves_weak_quarter_dissonance,
        #     self._resolves_cambiata_tail,
        #     self._prepares_weak_half_note,
        #     self._resolves_dissonant_quarter_on_weak_half_note,
        #     self._resolves_passing_half_note,
        #     self._handles_hiddens,
        #     self._handles_parallels,
        #     self._handles_doubled_leading_tone
        # ]
        self._melodic_rhythm_filters = [
            self._handles_runs,
            self._handles_consecutive_quarters,
            self._handles_penultimate_bar,
            self._handles_first_eighth,
            self._handles_sharp_durations,
            # self._handles_whole_note_quota,
            self._handles_repeated_note,
            self._handles_rhythm_after_descending_quarter_leap,
            self._handles_dotted_whole_after_quarters,
            self._handles_repeated_dotted_halfs,
            self._handles_antipenultimate_rhythm,
            # self._handles_half_note_chain,
            self._handles_missing_syncopation,
            self._handles_quarters_after_whole,
            self._handles_repetition_on_consecutive_syncopated_measures
        ]
        # self._harmonic_rhythm_filters = [
        #     self._prepares_suspension,
        #     self._resolves_cambiata,
        #     self._handles_weak_half_note_dissonance,
        # ]
        self._index_checks = [
            self._highest_and_lowest_placed
        ]
        self._change_params = [
            self._check_for_highest_and_lowest,
            # self._check_for_on_beat_whole_note,
            # self._check_if_new_run_is_added,
            self._check_if_eighths_are_added
        ]
        self._final_checks = [
            # self._parameters_are_correct,
            self._has_only_one_octave,
            self._no_unresolved_leading_tones
        ]
        self._params = [
            "highest_has_been_placed", "lowest_has_been_placed",
            "eighths_have_been_placed"
        ]

    def print_counterpoint(self):
        print("     LOWER:                   UPPER:")
        for i in range(self._length):
            for j in range(4):
                lower_note = str(self._counterpoint_obj[0][(i, j)]) if (i, j) in self._counterpoint_obj[0] else "                  "
                if (i, j + 0.5) in self._counterpoint_obj[0]:
                    lower_note += " " + str(self._counterpoint_obj[0][(i, j + .5)])
                upper_note = str(self._counterpoint_obj[1][(i, j)]) if (i, j) in self._counterpoint_obj[1] else "                  "
                if (i, j + 0.5) in self._counterpoint_obj[1]:
                    lower_note += " " + str(self._counterpoint_obj[1][(i, j + .5)])
                index_display = str(i) + ":" if j == 0 else ""
                print(index_display.ljust(5), lower_note.ljust(25), upper_note.ljust(25))

    def get_optimal(self):
        if len(self._solutions) == 0:
            return None 
        optimal = self._solutions[0]
        self._map_solution_onto_counterpoint_dict(optimal)
        self.print_counterpoint()
        return optimal

    def generate_2pfc(self):
        print("MODE = ", self._mode.value["name"])
        self._solutions = []
        def attempt():
            self._num_backtracks = 0
            self._solutions_this_attempt = 0
            initialized = self._initialize()
            self._backtrack()
        attempts = 0
        while len(self._solutions) < 100 and attempts < 1:
            attempts += 1
            print("attempt", attempts)
            attempt()
        print("number of attempts:", attempts)
        print("number of solutions:", len(self._solutions))
        if len(self._solutions) > 0:
            shuffle(self._solutions)
            self._solutions.sort(key = lambda sol: self._score_solution(sol)) 

    def _initialize(self) -> bool:
        indices = [[], []]
        for line in range(2):
            for bar in range(self._length - 1):
                for beat in [0, 1, 1.5, 2, 3]:
                    indices[line].append((bar, beat))
            indices[line].append((self._length - 1, 0))
        self._all_indices = [indices[line][:] for line in range(2)]
        self._remaining_indices = [indices[line][:] for line in range(2)]
        for line in range(2):
            self._remaining_indices[line].reverse()
        #initialize counterpoint data structure, that will map indices to notes
        self._counterpoint_obj = [{}, {}]
        for line in range(2):
            for index in self._all_indices[line]:
                self._counterpoint_obj[line][index] = None 
        #also initialize counterpoint data structure as list 
        self._counterpoint_lst = [[], []]
        #initialize parameters for this attempt
        self._attempt_params = [[], []] 
        for line in range(2): self._attempt_params[line] = {
            "lowest": None, "highest": None, "highest_must_appear_by": None, "lowest_must_appear_by": None, 
            "highest_has_been_placed": False, "lowest_has_been_placed": False,
            "eighths_have_been_placed": False, "run_indices": set()
        }
        vocal_range = [randint(8, 10), randint(8, 10)]
        for line in range(2):
            self._attempt_params[line]["lowest"] = self._mr[line].get_default_note_from_interval(self._mr[line].get_lowest(), randint(1, 13 - vocal_range[line]))
            self._attempt_params[line]["highest"] = self._mr[line].get_default_note_from_interval(self._attempt_params[line]["lowest"], vocal_range[line])
            self._attempt_params[line]["highest_must_appear_by"] = randint(3, self._length - 1)
            self._attempt_params[line]["lowest_must_appear_by"] = randint(3 if self._attempt_params[line]["highest_must_appear_by"] >= 5 else 5, self._length - 1)

        self._place_runs()

        self._store_params_stack = [[], []]
        self._stored_all_indices_stack = [[], []]
        self._stored_remaining_indices_stack = [[], []]
        self._stored_deleted_indices_stack = [[], []]
        self._valid_pitches = [[], []] 
        for line in range(2):
            valid_pitches = [self._attempt_params[line]["lowest"], self._attempt_params[line]["highest"]]
            for i in range(2, vocal_range[line]):
                valid_pitches += self._mr[line].get_notes_from_interval(self._attempt_params[line]["lowest"], i)
            self._valid_pitches[line] = valid_pitches
        
        return True 

    def _place_runs(self) -> None:
        run_lengths = [randint(5, 11), randint(5, 11)]
        start_beats = [0, 0]
        start_beats[0] = randint(3, (self._length - 2) * 4 - run_lengths[0] - run_lengths[1] + 3)
        while start_beats[0] % 4 == 0:
            start_beats[0] = randint(3, (self._length - 2) * 4 - run_lengths[0] - run_lengths[1] + 3)
        start_beats[1] = randint(start_beats[0] + run_lengths[0] - 3, (self._length - 2) * 4 - run_lengths[1])
        while start_beats[1] % 4 == 0:
            start_beats[1] = randint(start_beats[0] + run_lengths[0] - 3, (self._length - 2) * 4 - run_lengths[1])
    
        for line in range(2):
            for j in range(run_lengths[line]):
                total_beats = start_beats[line] + j 
                index = (total_beats // 4, total_beats % 4)
                self._attempt_params[line]["run_indices"].add(index)

    def _backtrack(self) -> None:
        if (self._num_backtracks > 100000) or (self._solutions_this_attempt > 0) or (self._solutions_this_attempt == 0 and self._num_backtracks > 100000):
            return 
        self._num_backtracks += 1
        if self._num_backtracks % 10000 == 0:
            print("backtrack number:", self._num_backtracks)
        if len(self._remaining_indices[0]) == 0 and len(self._remaining_indices[1]) == 0:
            if self._passes_final_checks():
                if self._solutions_this_attempt == 0:
                    print("FOUND SOLUTION!")
                self._solutions.append([self._counterpoint_lst[0][:], self._counterpoint_lst[1][:]])
                print(self._solutions[0])
                print("ALL INDICES:")
                print(self._all_indices)
                self._solutions_this_attempt += 1
            return 
        line = 0
        if len(self._remaining_indices[0]) == 0: line = 1
        elif len(self._remaining_indices[1]) == 0: line = 0
        elif self._remaining_indices[0][-1] > self._remaining_indices[1][-1]: line = 1
        elif self._remaining_indices[0][-1] == self._remaining_indices[1][-1] and random() < .5: line = 1

        (bar, beat) = self._remaining_indices[line].pop() 
        if self._passes_index_checks((bar, beat), line):
            candidates = list(filter(lambda n: self._passes_insertion_checks(n, (bar, beat), line), self._valid_pitches[line]))
            shuffle(candidates)
            if bar == 0 and beat == 0: candidates.append(Note(1, 0, 4, accidental=ScaleOption.REST))
            # print("candidates for index", bar, beat, ": ", len(candidates))
            notes_to_insert = []
            for candidate in candidates: 
                durations = self._get_valid_durations(candidate, (bar, beat), line)
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
        if bar == 0 and (beat == 0 or (beat == 2 and self._counterpoint_lst[line][0].get_accidental() == ScaleOption.REST)):
            return self._check_starting_pitch(note, line)
        if bar == self._length - 1:
            if not self._check_last_pitch(note, line): return False
        for check in self._melodic_insertion_checks:
            if not check(note, (bar, beat), line): 
                # print("failed insertion check:", str(note), index, "on function", check.__name__)
                return False 
        # print("passed insertion checks!", str(note), index)
        # for check in self._harmonic_insertion_checks:
        #     if not check(note, (bar, beat), line): 
        #         # print("failed insertion check:", str(note), index, "on function", check.__name__)
        #         return False 
        return True 

    def _get_valid_durations(self, note: Note, index: tuple, line: int) -> set:
        (bar, beat) = index 
        if bar == self._length - 1: return { 16 }
        if note.get_accidental() == ScaleOption.REST: return { 4 }
        if bar == 0 and beat == 0: return self._get_first_beat_options(note, line)
        durs = self._get_durations_from_beat(index)
        for check in self._melodic_rhythm_filters:
            durs = check(note, index, line, durs)
            if len(durs) == 0: break
        # for check in self._harmonic_rhythm_filters:
        #     durs = check(note, index, line, durs)
        #     if len(durs) == 0: break
        return durs 

    def _insert_note(self, note: Note, index: tuple, line: int) -> set:
        self._counterpoint_lst[line].append(note)
        self._counterpoint_obj[line][index] = note
        self._store_params_stack[line].append({})
        for param in self._params:
            self._store_params_stack[line][-1][param] = self._attempt_params[line][param]
        self._bury_indices(note, index, line)
        for check in self._change_params:
            check(note, index, line)

    def _remove_note(self, note: Note, index: tuple, line: int) -> set:
        self._counterpoint_lst[line].pop()
        self._counterpoint_obj[line][index] = None
        for param in self._params:
            self._attempt_params[line][param] = self._store_params_stack[line][-1][param]
        self._store_params_stack[line].pop()
        self._unbury_indices(note, index, line)

    def _passes_final_checks(self) -> bool:
        for check in self._final_checks:
            if not check(): 
                # print("failed final check:", check.__name__)
                return False 
        return True 

    ######################################
    ### melodic insertion checks #########

    def _check_starting_pitch(self, note: Note, line: int) -> bool:
        c_note = self._get_counterpoint_note((0, 0), line)
        if note.get_accidental() == ScaleOption.REST:
            if c_note is not None and c_note.get_accidental() == ScaleOption.REST: 
                return False 
            return True 
        if c_note is None or c_note.get_accidental() == ScaleOption.REST:
            return note.get_scale_degree() == self._mr[line].get_final() and note.get_accidental() == ScaleOption.NATURAL
        return c_note.get_scale_degree_interval(note) in  [-8, 1, 5, 8] and note.get_accidental() == ScaleOption.NATURAL
        
    def _check_last_pitch(self, note: Note, line: int) -> bool:
        c_note = self._get_counterpoint_note((0, 0), line) 
        if c_note is not None:
            return c_note.get_scale_degree_interval(note) in  [-8, 1, 5, 8] and note.get_accidental() == ScaleOption.NATURAL
        return self._mr[line].get_final() == note.get_scale_degree() and note.get_accidental() == ScaleOption.NATURAL

    def _handles_adjacents(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        (sdg_interval, chro_interval) = self._mr[line].get_intervals(self._counterpoint_lst[line][-1], note)
        if sdg_interval not in LegalIntervalsFifthSpecies["adjacent_melodic_scalar"]: 
            return False 
        if chro_interval not in LegalIntervalsFifthSpecies["adjacent_melodic_chromatic"]: 
            return False 
        if (sdg_interval, chro_interval) in LegalIntervalsFifthSpecies["forbidden_combinations"]: 
            return False 
        return True 

    def _handles_interval_order(self, note: Note, index: tuple, line: int) -> bool:
        potential_interval = self._counterpoint_lst[line][-1].get_scale_degree_interval(note)
        if potential_interval >= 3:
            for i in range(len(self._counterpoint_lst[line]) - 2, -1, -1):
                interval = self._counterpoint_lst[line][i].get_scale_degree_interval(self._counterpoint_lst[line][i + 1])
                if interval < 0: return True 
                if interval > 2: return False 
        if potential_interval == 2:
            segment_has_leap = False
            for i in range(len(self._counterpoint_lst[line]) - 2, -1, -1):
                interval = self._counterpoint_lst[line][i].get_scale_degree_interval(self._counterpoint_lst[line][i + 1])
                if interval < 0: return True 
                if segment_has_leap: return False 
                segment_has_leap = interval > 2
        if potential_interval == -2:
            segment_has_leap = False
            for i in range(len(self._counterpoint_lst[line]) - 2, -1, -1):
                interval = self._counterpoint_lst[line][i].get_scale_degree_interval(self._counterpoint_lst[line][i + 1])
                if interval > 0: return True 
                if segment_has_leap or interval == -8: return False 
                segment_has_leap = interval < -2
        if potential_interval <= -3:
            for i in range(len(self._counterpoint_lst[line]) - 2, -1, -1):
                interval = self._counterpoint_lst[line][i].get_scale_degree_interval(self._counterpoint_lst[line][i + 1])
                if interval > 0: return True 
                if interval < -2: return False 
        return True 

    def _handles_nearby_augs_and_dims(self, note: Note, index: tuple, line: int) -> bool:
        if len(self._counterpoint_lst[line]) < 2: return True
        if self._mr[line].is_cross_relation(note, self._counterpoint_lst[line][-2]) and self._counterpoint_lst[line][-1].get_duration() <= 2: return False 
        if self._counterpoint_lst[line][-2].get_duration() != 2 and self._counterpoint_lst[line][-1].get_duration() != 2: return True 
        (sdg_interval, chro_interval) = self._mr[line].get_intervals(self._counterpoint_lst[line][-2], note)
        return (abs(sdg_interval) != 2 or abs(chro_interval) != 3) and (abs(sdg_interval) != 3 or abs(chro_interval) != 2)

    def _handles_nearby_leading_tones(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if beat == 2 and (bar - 1, 2) in self._counterpoint_obj[line] and self._counterpoint_obj[line][(bar - 1, 2)].get_duration() > 4:
            if self._mr[line].is_sharp(self._counterpoint_obj[line][(bar - 1, 2)]) and self._counterpoint_obj[line][(bar - 1, 2)].get_chromatic_interval(note) != 1:
                return False 
        if beat == 0 and bar != 0:
            for i, num in enumerate([0, 1, 1.5, 2, 3]):
                if (bar - 1, num) in self._counterpoint_obj[line] and self._mr[line].is_sharp(self._counterpoint_obj[line][(bar - 1, num)]):
                    resolved = False
                    for j in range(i + 1, 5):
                        next_index = (bar - 1, [0, 1, 1.5, 2, 3][j])
                        if next_index in self._counterpoint_obj[line] and self._counterpoint_obj[line][(bar - 1, num)].get_chromatic_interval(self._counterpoint_obj[line][next_index]) == 1:
                            resolved = True 
                    if not resolved and self._counterpoint_obj[line][(bar - 1, num)].get_chromatic_interval(note) != 1:
                        return False 
        return True 

    def _handles_ascending_minor_sixth(self, note: Note, index: tuple, line: int) -> bool:
        if len(self._counterpoint_lst[line]) < 2: return True 
        if self._counterpoint_lst[line][-2].get_chromatic_interval(self._counterpoint_lst[line][-1]) == 8:
            return self._counterpoint_lst[line][-1].get_chromatic_interval(note) == -1
        return True

    def _handles_ascending_quarter_leaps(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if self._counterpoint_lst[line][-1].get_scale_degree_interval(note) > 2:
            if beat % 2 == 1: return False 
            if len(self._counterpoint_lst[line]) >= 2 and self._counterpoint_lst[line][-1].get_duration() == 2:
                if self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1]) > 0: return False
        return True 

    def _handles_descending_quarter_leaps(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if len(self._counterpoint_lst[line]) < 2: return True 
        if self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1]) < -2 and self._counterpoint_lst[line][-1].get_duration() == 2:
            if self._counterpoint_lst[line][-1].get_scale_degree_interval(note) == 2: return True 
            return self._counterpoint_lst[line][-2].get_scale_degree_interval(note) in [-2, 1, 2]
        return True 

    def _handles_repetition(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if self._mr[line].is_unison(self._counterpoint_lst[line][-1], note) and (beat != 2 or self._counterpoint_lst[line][-1].get_duration() != 2):
            return False 
        return True 

    def _handles_eigths(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if beat == 1.5 and abs(self._counterpoint_lst[line][-1].get_scale_degree_interval(note)) != 2: return False 
        if beat != 2: return True 
        if self._counterpoint_lst[line][-1].get_duration() != 1: return True 
        first_interval = self._counterpoint_lst[line][-3].get_scale_degree_interval(self._counterpoint_lst[line][-2])
        second_interval = self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1])
        third_interval = self._counterpoint_lst[line][-1].get_scale_degree_interval(note)
        if abs(third_interval) != 2 or (second_interval == 2 and third_interval == -2) or (first_interval == 2 and second_interval == -2): return False 
        return True 

    def _handles_highest(self, note: Note, index: tuple, line: int) -> bool:
        if self._attempt_params[line]["highest_has_been_placed"] and self._mr[line].is_unison(self._attempt_params[line]["highest"], note):
            return False 
        return True 

    def _handles_resolution_of_anticipation(self, note: Note, index: tuple, line: int) -> bool:
        if len(self._counterpoint_lst[line]) < 2 or not self._mr[line].is_unison(self._counterpoint_lst[line][-2], self._counterpoint_lst[line][-1]):
            return True 
        return self._counterpoint_lst[line][-1].get_scale_degree_interval(note) == -2

    def _handles_repeated_two_notes(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if len(self._counterpoint_lst[line]) < 3: return True 
        if not self._mr[line].is_unison(self._counterpoint_lst[line][-3], self._counterpoint_lst[line][-1]) or not self._mr[line].is_unison(self._counterpoint_lst[line][-2], note):
            return True 
        if self._counterpoint_lst[line][-1].get_scale_degree_interval(note) != 2: return False 
        if self._counterpoint_lst[line][-2].get_duration() != 8 or beat != 0: return False 
        return True

    def _handles_quarter_between_two_leaps(self, note: Note, index: tuple, line: int) -> bool:
        if self._counterpoint_lst[line][-1].get_duration() != 2 or len(self._counterpoint_lst[line]) < 2: return True 
        first_interval, second_interval = self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1]), self._counterpoint_lst[line][-1].get_scale_degree_interval(note)
        if abs(first_interval) == 2 or abs(second_interval) == 2:
            return True 
        if first_interval > 0 and second_interval < 0: return False 
        if first_interval == -8 and second_interval == 8: return False 
        return True 

    def _handles_upper_neighbor(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if ( beat % 2 == 0 and self._counterpoint_lst[line][-1].get_duration() == 2 and  
            self._counterpoint_lst[line][-1].get_scale_degree_interval(note) == -2 and len(self._counterpoint_lst[line]) >= 2 and 
            self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1]) == 2 and 
            self._counterpoint_lst[line][-2].get_duration() != 2 ): return False 
        return True 

    def _handles_antipenultimate_bar(self, note: Note, index: tuple, line: int) -> bool:
        if index == (self._length - 3, 2):
            if note.get_accidental() != ScaleOption.NATURAL or note.get_scale_degree() != self._mr[line].get_final():
                return False 
        return True 

    ######################################
    ###### harmonic insertion checks ######

    def _filters_dissonance_on_downbeat(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index 
        if beat != 0: return True
        cf_note = self._cantus[bar]
        return self._is_consonant(cf_note, note)
        
    def _resolves_suspension(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat not in [1, 2] or (bar, 0) in self._counterpoint_obj: return True 
        susp_index = (bar - 1, 2) if (bar - 1, 2) in self._counterpoint_obj else (bar - 1, 0)
        cf_note, susp = self._cantus[bar], self._counterpoint_obj[susp_index]
        if cf_note.get_scale_degree_interval(susp) in LegalIntervalsFifthSpecies["resolvable_dissonance"]:
            return susp.get_scale_degree_interval(note) == -2
        return True 

    def _prepares_weak_quarter_dissonance(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat % 2 != 1 or self._is_consonant(self._cantus[bar], note): return True 
        if not self._is_consonant(self._cantus[bar], self._counterpoint_lst[-1]): return False 
        return abs(self._counterpoint_lst[-1].get_scale_degree_interval(note)) == 2

    def _resolves_weak_quarter_dissonance(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat % 2 != 0 or self._counterpoint_lst[-1].get_duration() != 2: return True 
        if self._is_consonant(self._cantus[bar if beat > 0 else bar - 1], self._counterpoint_lst[-1]): return True 
        first_interval = self._counterpoint_lst[-2].get_scale_degree_interval(self._counterpoint_lst[-1])
        second_interval = self._counterpoint_lst[-1].get_scale_degree_interval(note) 
        if second_interval not in [-3, -2, 1]: return False 
        if first_interval == 2 and second_interval == -3: return False 
        return True 

    def _resolves_cambiata_tail(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat == 1.5: return True 
        first_index, second_index = (bar - 1, 1), (bar - 1, 2)
        if beat in [1, 2]:
            first_index, second_index = (bar - 1, 3), (bar, 0)
        if beat == 3:
            first_index, second_index = (bar , 1), (bar, 2)
        if first_index not in self._counterpoint_obj or second_index not in self._counterpoint_obj: return True 
        cf_note = self._cantus[bar if beat == 3 else bar - 1]
        if not self._is_consonant(cf_note, self._counterpoint_obj[first_index]) and self._counterpoint_obj[first_index].get_scale_degree_interval(self._counterpoint_obj[second_index]) == -3:
            return self._counterpoint_lst[-1].get_scale_degree_interval(note) == 2
        return True 

    def _prepares_weak_half_note(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat != 2: return True 
        cf_note = self._cantus[bar]
        if self._is_consonant(cf_note, note): return True 
        if (bar, 0) not in self._counterpoint_obj or self._counterpoint_obj[(bar, 0)].get_duration() != 4: return False 
        return abs(self._counterpoint_obj[(bar, 0)].get_scale_degree_interval(note)) == 2

    def _resolves_dissonant_quarter_on_weak_half_note(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat != 3 or (bar, 2) not in self._counterpoint_obj: return True 
        if self._is_consonant(self._cantus[bar], self._counterpoint_obj[(bar, 2)]): return True 
        return self._counterpoint_obj[(bar, 2)].get_scale_degree_interval(note) == -2

    def _resolves_passing_half_note(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat != 0 or (bar - 1, 2) not in self._counterpoint_obj or self._counterpoint_obj[(bar - 1, 2)].get_duration() != 4: return True 
        if self._is_consonant(self._counterpoint_obj[(bar - 1, 2)], self._cantus[bar - 1]): return True 
        return self._counterpoint_lst[-2].get_scale_degree_interval(self._counterpoint_lst[-1]) == self._counterpoint_lst[-1].get_scale_degree_interval(note)

    def _handles_hiddens(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat != 0 or self._cantus[bar].get_chromatic_interval(note) not in [-19, -12, -7, 0, 7, 12, 19]: return True 
        upper_interval = self._counterpoint_lst[-1].get_scale_degree_interval(note)
        lower_interval = self._cantus[bar - 1].get_scale_degree_interval(self._cantus[bar])
        if (upper_interval > 0 and lower_interval > 0) or (upper_interval < 0 and lower_interval < 0): return False 
        return True 

    def _handles_parallels(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat == 2 and self._counterpoint_lst[-1].get_duration() >= 8 and self._cantus[bar].get_chromatic_interval(note) in [-19, -12, 0, 12, 19]:
            return self._cantus[bar].get_chromatic_interval(note) != self._cantus[bar - 1].get_chromatic_interval(self._counterpoint_lst[-1])
        if beat != 0 or self._cantus[bar].get_chromatic_interval(note) not in [-19, -12, 0, 12, 19]: return True 
        if (bar - 1, 2) in self._counterpoint_obj and self._cantus[bar - 1].get_chromatic_interval(self._counterpoint_obj[(bar - 1, 2)]) == self._cantus[bar].get_chromatic_interval(note):
            return False 
        index_to_check = (bar - 1, 0)
        if index_to_check not in self._counterpoint_obj or self._counterpoint_obj[index_to_check].get_duration() == 2: 
            return True 
        if self._cantus[bar - 1].get_chromatic_interval(self._counterpoint_obj[index_to_check]) == self._cantus[bar].get_chromatic_interval(note):
            return False
        return True 

    def _handles_doubled_leading_tone(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat != 0 or self._cantus[bar].get_chromatic_interval(note) not in [-12, 0, 12]: return True 
        if (note.get_scale_degree() + 1) % 7 == self._mr.get_final(): return False 
        return True 

    ######################################
    ###### melodic rhythms filters #######

    def _handles_runs(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index
        if index in self._attempt_params[line]["run_indices"]: 
            return { 2 } if 2 in durs else set()
        if (bar, beat + 1) in self._attempt_params[line]["run_indices"]: 
            for d in [4, 6, 8, 12]: durs.discard(d)
        two_beats_next = (bar, beat + 2) if beat == 0 else (bar + 1, 0)
        if two_beats_next in self._attempt_params[line]["run_indices"]: 
            for d in [2, 6, 8, 12]: durs.discard(d)
        three_beats_next = (bar, beat + 3) if beat == 0 else (bar + 1, 1)
        if three_beats_next in self._attempt_params[line]["run_indices"]: 
            for d in [2, 8, 12]: durs.discard(d)
        if (bar + 1, 2) in self._attempt_params[line]["run_indices"]:
            durs.discard(12)
        return durs

    def _get_durations_from_beat(self, index: tuple) -> set:
        (bar, beat) = index
        if beat == 1.5: return { 1 }
        if beat == 3: return { 2 }
        if beat == 1: return { 1, 2 }
        if beat == 2: return { 2, 4, 6, 8 }
        if beat == 0: return { 2, 4, 6, 8, 12 } if bar == 0 else { 2, 4, 6, 8 }

    def _handles_consecutive_quarters(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index
        if self._counterpoint_lst[line][-1].get_duration() != 2: return durs 
        if self._counterpoint_lst[line][-1].get_scale_degree_interval(note) > 0 and beat == 2: durs.discard(4)
        if beat == 2 and self._counterpoint_lst[line][-2].get_duration() == 2 and self._counterpoint_lst[line][-3].get_duration() != 2:
            durs.discard(4)
        for i in range(len(self._counterpoint_lst[line]) - 2, -1, -1):
            if self._counterpoint_lst[line][i].get_duration() != 2:
                return durs 
            if abs(self._counterpoint_lst[line][i].get_scale_degree_interval(self._counterpoint_lst[line][i + 1])) > 2:
                durs.discard(2)
                return durs 

    def _handles_penultimate_bar(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index 
        if bar != self._length - 2: return durs 
        if beat == 2: 
            durs.discard(8)
            durs.discard(6)
            durs.discard(2)
        if beat == 0:
            durs.discard(12)
            durs.discard(6)
            durs.discard(4)
        return durs

    def _handles_first_eighth(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index 
        if (beat == 1 and abs(self._counterpoint_lst[line][-1].get_scale_degree_interval(note)) != 2) or self._attempt_params[line]["eighths_have_been_placed"]:
            durs.discard(1)
        if beat == 2 and self._counterpoint_lst[line][-1].get_duration() == 1 and self._counterpoint_lst[line][-3].get_duration() == 2:
            durs.discard(4)
            durs.discard(8)
            durs.discard(6)
        return durs 

    def _handles_sharp_durations(self, note: Note, index: tuple, line: int, durs: set) -> set:
        if self._mr[line].is_sharp(note): durs.discard(12)
        return durs 

    # def _handles_whole_note_quota(self, note: Note, index: tuple, durs: set) -> set:
    #     (bar, beat) = index 
    #     if self._attempt_params["num_on_beat_whole_notes_placed"] == self._attempt_params["max_on_beat_whole_notes"]:
    #         if beat == 0: 
    #             durs.discard(8) 
    #             durs.discard(12)
    #     return durs

    def _handles_repeated_note(self, note: Note, index: tuple, line: int, durs: set) -> set:
        if self._mr[line].is_unison(self._counterpoint_lst[line][-1], note): 
            durs.discard(4)
            durs.discard(2)
        return durs

    def _handles_rhythm_after_descending_quarter_leap(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index
        if self._counterpoint_lst[line][-1].get_duration() == 2 and self._counterpoint_lst[line][-1].get_scale_degree_interval(note) < -2:
            durs.discard(8)
            durs.discard(12)
            durs.discard(6)
        return durs

    def _handles_dotted_whole_after_quarters(self, note: Note, index: tuple, line: int, durs: set) -> set:
        if self._counterpoint_lst[line][-1].get_duration() == 2: durs.discard(12)
        return durs

    def _handles_repeated_dotted_halfs(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index 
        if beat != 0: return durs 
        if (bar - 1, 0) in self._counterpoint_obj[line] and self._counterpoint_obj[line][(bar - 1, 0)].get_duration() == 6:
            durs.discard(6)
        if bar % 2 == 0 and (bar - 2, 0) in self._counterpoint_obj[line] and self._counterpoint_obj[line][(bar - 2, 0)].get_duration() == 6:  
            durs.discard(6) 
        return durs

    def _handles_antipenultimate_rhythm(self, note: Note, index: tuple, line: int, durs: set) -> set:
        if index == (self._length - 3, 2): 
            if (self._length - 2, 0) in self._counterpoint_obj[(line + 1) % 2]:
                durs.discard(4)
                durs.discard(2)
            if (self._length - 2, 0) not in self._counterpoint_obj[(line + 1) % 2]:
                durs.discard(8)
                durs.discard(6)
        return durs 

    # def _handles_half_note_chain(self, note: Note, index: tuple, durs: set) -> set:
    #     (bar, beat) = index
    #     if beat == 2 and len(self._counterpoint_lst) >= 3:
    #         if self._counterpoint_lst[-3].get_duration() == 4 and self._counterpoint_lst[-2].get_duration() == 4 and self._counterpoint_lst[-1].get_duration() == 4:
    #             durs.discard(4)
    #     return durs

    def _handles_missing_syncopation(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index 
        if beat != 0 or (bar - 1, 0) not in self._counterpoint_obj[line] or (bar - 2, 0) not in self._counterpoint_obj[line] or (bar - 3, 0) not in self._counterpoint_obj[line]:
            return durs 
        if self._counterpoint_obj[line][(bar - 3, 0)].get_duration() >= 4 and self._counterpoint_obj[line][(bar - 2, 0)].get_duration() >= 4 and self._counterpoint_obj[line][(bar - 1, 0)].get_duration() >= 4:
            durs.discard(4)
            durs.discard(6)
            durs.discard(8)
        return durs

    def _handles_quarters_after_whole(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index
        if beat == 0 and self._counterpoint_lst[line][-1].get_duration() == 8:
            durs.discard(2)
        return durs
        
    def _handles_repetition_on_consecutive_syncopated_measures(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index 
        if beat == 2 and (bar, 0) not in self._counterpoint_obj[line] and (bar - 1, 2) in self._counterpoint_obj[line] and self._mr[line].is_unison(self._counterpoint_obj[line][(bar - 1, 2)], note):
            durs.discard(6)
            durs.discard(8)
        return durs



    ##########################################
    ###### harmonic rhythm filters ###########

    def _get_first_beat_options(self, note: Note, line: int) -> set:
        durs = { 4, 6, 8, 12 }
        # if not self._is_consonant(self._cantus[1], note) and self._cantus[1].get_scale_degree_interval(note) not in LegalIntervalsFifthSpecies["resolvable_dissonance"]:
        #     durs.discard(12)
        return durs

    def _prepares_suspension(self, note: Note, index: tuple, durs: set) -> set:
        (bar, beat) = index 
        if bar == self._length - 1 or self._is_consonant(self._cantus[bar + 1], note): return durs 
        if self._cantus[bar + 1].get_scale_degree_interval(note) in LegalIntervalsFifthSpecies["resolvable_dissonance"]:
            return durs 
        if beat == 0:
            durs.discard(12)
        if beat == 2:
            durs.discard(8)
            durs.discard(6)
        return durs 

    def _resolves_cambiata(self, note: Note, index: tuple, durs: set) -> set:
        (bar, beat) = index 
        if beat % 2 != 0: return durs 
        index_to_check = (bar - 1, 3) if beat == 0 else (bar, 1)
        if index_to_check not in self._counterpoint_obj: return durs 
        if self._is_consonant(self._cantus[bar - 1 if beat == 0 else bar], self._counterpoint_obj[index_to_check]): return durs 
        if self._counterpoint_obj[index_to_check].get_scale_degree_interval(note) != -3: return durs 
        durs.discard(12)
        durs.discard(8)
        durs.discard(6)
        return durs 

    def _handles_weak_half_note_dissonance(self, note: Note, index: tuple, durs: set) -> set:
        (bar, beat) = index 
        if beat != 2 or self._is_consonant(self._cantus[bar], note): return durs 
        durs.discard(6)
        durs.discard(8)
        if self._counterpoint_lst[-1].get_scale_degree_interval(note) == 2:
            durs.discard(2)
        return durs
        

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

    def _bury_indices(self, note: Note, index: tuple, line: int) -> None:
        (bar, beat) = index
        self._stored_all_indices_stack[line].append(self._all_indices[line][:])
        self._stored_remaining_indices_stack[line].append(self._remaining_indices[line][:])
        self._stored_deleted_indices_stack[line].append([])
        for i in range(1, note.get_duration()):
            new_beat, new_bar = beat + (i / 2), bar
            while new_beat >= 4:
                new_beat -= 4
                new_bar += 1
            if (new_bar, new_beat) in self._counterpoint_obj[line]:
                del self._counterpoint_obj[line][(new_bar, new_beat)]
                self._all_indices[line].remove((new_bar, new_beat))
                self._remaining_indices[line].remove((new_bar, new_beat))
                self._stored_deleted_indices_stack[line][-1].append((new_bar, new_beat))

    def _unbury_indices(self, note: Note, index: tuple, line: int) -> None:
        self._all_indices[line] = self._stored_all_indices_stack[line].pop()
        self._remaining_indices[line] = self._stored_remaining_indices_stack[line].pop()
        for index in self._stored_deleted_indices_stack[line].pop():
            self._counterpoint_obj[line][index] = None

    def _check_for_highest_and_lowest(self, note: Note, index: tuple, line: int) -> None:
        if self._mr[line].is_unison(note, self._attempt_params[line]["highest"]):
            self._attempt_params[line]["highest_has_been_placed"] = True 
        if self._mr[line].is_unison(note, self._attempt_params[line]["lowest"]):
            self._attempt_params[line]["lowest_has_been_placed"] = True 

    # def _check_for_on_beat_whole_note(self, note: Note, index: tuple, line: int) -> None:
    #     (bar, beat) = index 
    #     if beat == 0 and note.get_duration() >= 8:
    #         self._attempt_params[line]["num_on_beat_whole_notes_placed"] += 1

    # def _check_if_new_run_is_added(self, note: Note, index: tuple) -> None:
    #     run_length = 0
    #     for i in range(len(self._counterpoint_lst) - 1, -1, -1):
    #         dur = self._counterpoint_lst[i].get_duration()
    #         if dur > 2: 
    #             break 
    #         run_length += dur / 2
    #     if run_length == 4:
    #         self._attempt_params["num_runs_placed"] += 1
    #     if run_length == self._attempt_params["min_length_of_max_quarter_run"]:
    #         self._attempt_params["max_quarter_run_has_been_placed"] = True 

    def _check_if_eighths_are_added(self, note: Note, index: tuple, line: int) -> None:
        (bar, beat) = index 
        if beat == 1.5: 
            for line in range(2):
                self._attempt_params[line]["eighths_have_been_placed"] = True

    ##########################################
    ########### final checks #################

    def _parameters_are_correct(self) -> bool:
        # print("num runs placed:", self._attempt_params["num_runs_placed"])
        # print("max run has been placed?", self._attempt_params["max_quarter_run_has_been_placed"])
        return self._attempt_params["num_runs_placed"] >= self._attempt_params["min_runs_of_length_4_or_more"] and self._attempt_params["max_quarter_run_has_been_placed"]

    def _has_only_one_octave(self) -> bool:
        for line in range(2):
            num_octaves = 0
            for i in range(0 if self._counterpoint_lst[line][0].get_accidental() != ScaleOption.REST else 1, len(self._counterpoint_lst[line]) - 1):
                if abs(self._counterpoint_lst[line][i].get_scale_degree_interval(self._counterpoint_lst[line][i + 1])) == 8:
                    num_octaves += 1
                    if num_octaves > 1: 
                        return False 
        return True 

    def _no_unresolved_leading_tones(self) -> bool:
        for line in range(2):
            for i in range(1, self._length - 2):
                if (i, 0) not in self._counterpoint_obj[line]:
                    notes_to_check = []
                    for index in [(i - 1, 0), (i - 1, 1), (i - 1, 2), (i, 2)]:
                        if index in self._counterpoint_obj[line]: notes_to_check.append(self._counterpoint_obj[line][index])
                    for j, note in enumerate(notes_to_check):
                        if self._mr[line].is_sharp(note):
                            resolved = False 
                            for k in range(j + 1, len(notes_to_check)):
                                if note.get_chromatic_interval(notes_to_check[k]) == 1:
                                    resolved = True 
                            if not resolved: return False 
        return True 


    ##########################################
    ########### scoring ######################

    def _score_solution(self, solution: list[list[Note]]) -> int:
        score = 0
        self._map_solution_onto_counterpoint_dict(solution)
        for line in range(2):
            num_ties = 0
            num_tied_dotted_halfs = 0
            num_tied_wholes = 0
            ties = [False] * (self._length - 2)
            for i in range(1, self._length - 1):
                if (i, 0) not in self._counterpoint_obj[line]: 
                    ties[i - 1] = True
                    num_ties += 1
                    if (i - 1, 2) in self._counterpoint_obj[line]:
                        if self._counterpoint_obj[line][(i - 1, 2)].get_duration() == 6:
                            num_tied_dotted_halfs += 1
                        else:
                            num_tied_wholes += 1
            ideal_ties = 3 if self._length < 12 else 4 
            score += abs(ideal_ties - num_ties) * 10 
            score += abs(num_tied_wholes - num_tied_dotted_halfs) * 5
            has_isolated_tie = False
            for i in range(1, len(ties) - 1):
                if ties[i - 1] == False and ties[i] == True and ties[i + 1] == False:
                    has_isolated_tie = True 
            if has_isolated_tie: score -= 12
            num_quarter_runs_starting_on_beat = 0
            num_quarter_runs_starting_on_beat_of_length_two = 0
            num_other_two_note_quarter_runs = 0
            for i, index in enumerate(self._all_indices[line]):
                (bar, beat) = index 
                if beat == 0 and self._counterpoint_lst[line][i].get_duration() == 2 and self._counterpoint_lst[line][i - 1].get_duration() != 2:
                    num_quarter_runs_starting_on_beat += 1
                    if self._counterpoint_lst[line][i + 2].get_duration() != 2:
                        num_quarter_runs_starting_on_beat_of_length_two += 1
                if beat == 2 and self._counterpoint_lst[line][i].get_duration() == 2 and self._counterpoint_lst[line][i - 1].get_duration() != 2:
                    if self._counterpoint_lst[line][i + 2].get_duration() != 2:
                        num_other_two_note_quarter_runs += 1
            score += num_quarter_runs_starting_on_beat * 60 + num_quarter_runs_starting_on_beat_of_length_two * 60 + num_other_two_note_quarter_runs * 45
            # num_fifths, num_octaves = 0, 0
            # for i in range(1, self._length - 2):
            #     if (i, 0) in self._counterpoint_obj:
            #         intvl = self._cantus[i].get_chromatic_interval(self._counterpoint_obj[(i, 0)])
            #         if intvl in [-19, -7, 7, 19]: num_fifths += 1
            #         elif intvl in [-12, 0, 12]: num_octaves += 1
            # score += num_fifths * 30 + num_octaves * 10
            num_steps = 0
            for i in range(len(self._counterpoint_lst[line]) - 1):
                if abs(self._counterpoint_lst[line][i].get_scale_degree_interval(self._counterpoint_lst[line][i + 1])) == 2:
                    num_steps += 1
            score += math.floor(150 * abs(.712 - (num_steps / (len(self._counterpoint_lst[line]) - 1))))
        return score 

    def _map_solution_onto_counterpoint_dict(self, solution: list[list[Note]]) -> None:
        for line in range(2):
            self._counterpoint_obj[line] = {}
            self._counterpoint_lst[line] = []
            self._all_indices[line] = []
            bar, beat = 0, 0
            for note in solution[line]:
                self._counterpoint_obj[line][(bar, beat)] = note
                self._counterpoint_lst[line].append(note)
                self._all_indices[line].append((bar, beat))
                beat += note.get_duration() / 2 
                while beat >= 4:
                    beat -= 4
                    bar += 1

    def _is_consonant(self, note1: Note, note2: Note) -> bool:
        (sdg_interval, chro_interval) = self._mr.get_intervals(note1, note2)
        if sdg_interval not in LegalIntervalsFifthSpecies["harmonic_scalar"]: return False 
        if chro_interval not in LegalIntervalsFifthSpecies["harmonic_chromatic"]: return False 
        if (sdg_interval, chro_interval) in LegalIntervalsFifthSpecies["forbidden_combinations"]: return False 
        return True 

    def _get_counterpoint_note(self, index: tuple, line: int) -> Note:
        (bar, beat), other_line = index, (line + 1) % 2
        while (bar, beat) not in self._counterpoint_obj[other_line]:
            beat -= 0.5 
            if beat < 0:
                beat += 4
                bar -= 1
        return self._counterpoint_obj[other_line][(bar, beat)]