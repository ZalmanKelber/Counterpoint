from random import random, shuffle, randint
import math
from time import time

from notation_system import ModeOption, ScaleOption, RangeOption, Note, ModeResolver, HexachordOption
from two_part_first_species import Orientation
from legal_intervals import LegalIntervalsFifthSpecies, MaxAcceptableRepetitions
from imitation_theme import GenerateImitationTheme

class GenerateImitation:

    def __init__(self, mode: ModeOption, first_highest: Note, first_lowest: Note, second_highest: Note, second_lowest):
        self._mode = mode
        self._mr = [ModeResolver(mode), ModeResolver(mode)]
        self._length = 20
        hexachords = [HexachordOption.DURUM, HexachordOption.MOLLE]
        shuffle(hexachords)
        self._attempt_params = []
        for line in range(2): self._attempt_params.append({
            "lowest": first_lowest if line == 0 else second_lowest, 
            "highest": first_highest if line == 0 else second_highest, 
            "hexachord": hexachords[line],
            "highest_has_been_placed": False,
            "theme_index": 0
        })
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
            self._handles_final_unsyncopated_whole_note,
            self._handles_contrary_motion_surrounding_quarter_note_octave_leap,
            self._handles_final_leading_tone,
            # self._handles_preset_suspension_resolution
        ]

        self._harmonic_insertion_checks = [
            self._filters_dissonance_on_downbeat,
            self._resolves_suspension,
            self._forms_suspension,
            self._prepares_weak_quarter_dissonance,
            self._resolves_weak_quarter_dissonance,
            self._resolves_cambiata_tail,
            self._prepares_weak_half_note,
            self._resolves_dissonant_quarter_on_weak_half_note,
            self._resolves_passing_half_note,
            self._handles_hiddens,
            self._handles_parallels,
            self._handles_doubled_leading_tone,
            self._no_vertical_cross_relations,
            self._no_diagonal_cross_relations,
            # self._forms_preset_suspension,
            # self._prevents_suspensions_from_resolving_to_perfect_intervals,
            self._sharp_moves_up_if_against_tritone,
            self._handles_landini
        ]

        self._melodic_rhythm_filters = [
            # self._handles_runs,
            self._handles_consecutive_quarters,
            self._handles_penultimate_bar,
            # self._handles_first_eighth,
            self._handles_sharp_durations,
            # self._handles_whole_note_quota,
            # self._handles_double_syncopation,
            # self._handles_repeated_note,
            # self._handles_rhythm_after_descending_quarter_leap,
            # self._handles_dotted_whole_after_quarters,
            # self._handles_repeated_dotted_halfs,
            # self._handles_antipenultimate_rhythm,
            # self._handles_half_note_chain,
            # self._handles_missing_syncopation,
            # self._handles_quarters_after_whole,
            # self._handles_repetition_on_consecutive_syncopated_measures,
            # self._prepares_preset_suspension_rhythmically
        ]
        self._harmonic_rhythm_filters = [
            self._prepares_suspension,
            self._resolves_cambiata,
            self._handles_weak_half_note_dissonance,
            self._forms_weak_quarter_dissonance,
            self._forms_weak_half_note_dissonance,
            self._doesnt_create_dissonance_on_following_measure,
            self._doesnt_create_dissonance_on_next_half_note
        ]
        self._index_checks = [
            # self._highest_and_lowest_placed
        ]
        self._change_params = [
            self._check_for_highest_and_lowest,
            # self._check_for_on_beat_whole_note,
            # self._check_if_new_run_is_added,
            self._increment_theme_index
        ]
        self._final_checks = [
            # self._parameters_are_correct,
            # self._has_only_two_octaves,
            # self._no_unresolved_leading_tones,
            # self._top_line_resolves_by_step
        ]
        self._params = [
            "theme_index"
        ]

    def print_counterpoint(self):
        length = 0
        for note in self._counterpoint_lst[1]: length += note.get_duration() / 8
        print("     LOWER:                   UPPER:")
        for i in range(math.ceil(length)):
            for j in range(4):
                lower_note = str(self._counterpoint_obj[0][(i, j)]) if (i, j) in self._counterpoint_obj[0] else "                  "
                upper_note = str(self._counterpoint_obj[1][(i, j)]) if (i, j) in self._counterpoint_obj[1] else "                  "
                index_display = str(i) + ":" if j == 0 else ""
                print(index_display.ljust(5), lower_note.ljust(28), upper_note.ljust(25))

    def get_optimal(self):
        if len(self._solutions) == 0:
            return None 
        optimal = self._solutions[0]
        self._map_solution_onto_counterpoint_dict(optimal)
        self.print_counterpoint()
        return optimal

    def generate_imitation(self):
        self._solutions = []
        def attempt():
            self._num_backtracks = 0
            self._found_possible = False
            self._solutions_this_attempt = 0
            initialized = self._initialize()
            self._backtrack()
        attempts = 0
        while len(self._solutions) < 10 and attempts < 100:
            attempts += 1
            attempt()
        # solutions:", len(self._solutions))
        if len(self._solutions) > 0:
            shuffle(self._solutions)
            self._solutions.sort(key = lambda sol: self._score_solution(sol)) 

    def _initialize(self) -> bool:
        self._all_indices = [[], []]
        self._remaining_indices = [[], []]
        self._counterpoint_lst = [[], []]
        self._counterpoint_obj = [{}, {}]
        git = GenerateImitationTheme(self._mode, self._attempt_params[0]["hexachord"], self._attempt_params[0]["highest"], self._attempt_params[0]["lowest"])
        git.generate_theme()
        theme = git.get_optimal()[0]
        theme_measures = 0
        for note in theme: theme_measures += note.get_duration() / 8
        self._theme_measures = theme_measures
        self._map_solution_onto_counterpoint_dict([theme, []])
        self._theme_length = len(theme)
        for bar in range(14):
            for beat in [0, 1, 2, 3]:
                self._all_indices[1].append((bar, beat))
        self._remaining_indices[1] = self._all_indices[1][:]
        self._remaining_indices[1].reverse()
        #initialize counterpoint data structure, that will map indices to notes
        for index in self._all_indices[1]:
            self._counterpoint_obj[1][index] = None 
        #initialize parameters for this attempt 
        self._store_params_stack = [[], []]
        self._stored_all_indices_stack = [[], []]
        self._stored_remaining_indices_stack = [[], []]
        self._stored_deleted_indices_stack = [[], []]
        self._valid_pitches = [[], []] 
        for line in range(2):
            self._valid_pitches[line] = [self._attempt_params[line]["lowest"], self._attempt_params[line]["highest"]]
            for i in range(2, self._attempt_params[line]["lowest"].get_scale_degree_interval(self._attempt_params[line]["highest"])):
                self._valid_pitches[line] += self._mr[line].get_notes_from_interval(self._attempt_params[line]["lowest"], i)
        return True 

    def _backtrack(self) -> None:
        # print("backtrack number:", self._num_backtracks, "theme index:", self._attempt_params[1]["theme_index"])
        if (self._num_backtracks > 10000) or (self._solutions_this_attempt > 500) or (not self._found_possible and self._num_backtracks > 1000):
            return 
        self._num_backtracks += 1
        if self._attempt_params[1]["theme_index"] >= self._theme_length:
            if not self._found_possible:
                self._found_possible = True 
                #print("found possible solution!  backtracks:", self._num_backtracks)
            if self._passes_final_checks():
                # if self._solutions_this_attempt == 0:
                    #print("FOUND SOLUTION!  backtracks:", self._num_backtracks)
                self._solutions.append([self._counterpoint_lst[0][:], self._counterpoint_lst[1][:]])
                self._solutions_this_attempt += 1
            return 
        
        line = 1
        (bar, beat) = self._remaining_indices[line].pop() 
        back_tracks_at_start = self._num_backtracks
        if self._passes_index_checks((bar, beat), line):
            candidates = list(filter(lambda n: self._passes_insertion_checks(n, (bar, beat), line), self._valid_pitches[line]))
            shuffle(candidates)
            # print("candidates for index", bar, beat, ": ", len(candidates))
            notes_to_insert = []
            for candidate in candidates: 
                durations = self._get_valid_durations(candidate, (bar, beat), line)
                for dur in durations:
                    notes_to_insert.append(Note(candidate.get_scale_degree(), candidate.get_octave(), dur, accidental=candidate.get_accidental()))
            shuffle(notes_to_insert)
            notes_to_insert.append(Note(1, 0, 8, ScaleOption.REST))
            for note_to_insert in notes_to_insert:
                if self._check_theme(note_to_insert, (bar, beat)):
                    if note_to_insert.get_accidental() == ScaleOption.REST and note_to_insert.get_duration() != 8:
                        print(note_to_insert)
                    self._insert_note(note_to_insert, (bar, beat), line)
                    self._backtrack()
                    self._remove_note(note_to_insert, (bar, beat), line)
                    if self._solutions_this_attempt > 0 and notes_to_insert[-1].get_accidental() == ScaleOption.REST:
                        notes_to_insert.pop()
        self._remaining_indices[line].append((bar, beat))

    def _check_theme(self, note: Note, index) -> bool:
        theme_index = self._attempt_params[1]["theme_index"]
        if note.get_accidental() == ScaleOption.REST: 
            if theme_index != 0: return False 
            if index[0] >= self._theme_measures - 2: return False 
            return True
        if theme_index == 0:
            transposition_interval = 5 if self._attempt_params[0]["hexachord"] == HexachordOption.MOLLE else 4
            if ( self._mr[1].get_default_note_from_interval(note, transposition_interval).get_scale_degree() == self._counterpoint_lst[0][0].get_scale_degree()
                and note.get_accidental() == ScaleOption.NATURAL): 
                return self._counterpoint_lst[0][0].get_duration() == note.get_duration()
            return False 
        if self._counterpoint_lst[1][-1].get_scale_degree_interval(note) == self._counterpoint_lst[0][theme_index - 1].get_scale_degree_interval(self._counterpoint_lst[0][theme_index]):
            return self._counterpoint_lst[0][theme_index].get_duration() == note.get_duration()
        return False

    def _passes_index_checks(self, index: tuple, line: int) -> bool:
        for check in self._index_checks:
            if not check(index, line): return False 
        return True

    def _passes_insertion_checks(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index 
        for check in self._melodic_insertion_checks:
            if not check(note, (bar, beat), line): 
                # if bar > 2:
                #     print(note,"failed insertion check", check.__name__, "at index", str((bar, beat)))
                return False 
        for check in self._harmonic_insertion_checks:
            if not check(note, (bar, beat), line): 
                return False 
        return True 

    def _get_valid_durations(self, note: Note, index: tuple, line: int) -> set:
        (bar, beat) = index 
        durs = { 16, 12, 8, 6, 4, 2 }
        for check in self._melodic_rhythm_filters:
            durs = check(note, index, line, durs)
            if len(durs) == 0: 
                break
        for check in self._harmonic_rhythm_filters:
            durs = check(note, index, line, durs)
            if len(durs) == 0: break
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
        if self._counterpoint_lst[line][-1].get_duration() < 8 and abs(self._counterpoint_lst[line][-1].get_scale_degree_interval(note)) != 2:
            return False
        c_note = self._get_counterpoint_note((0, 0), line) 
        if c_note is not None:
            return c_note.get_scale_degree_interval(note) in  [-8, 1, 5, 8] and note.get_accidental() == ScaleOption.NATURAL
        return self._mr[line].get_final() == note.get_scale_degree() and note.get_accidental() == ScaleOption.NATURAL

    def _handles_adjacents(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
        (sdg_interval, chro_interval) = self._mr[line].get_intervals(self._counterpoint_lst[line][-1], note)
        if sdg_interval not in LegalIntervalsFifthSpecies["adjacent_melodic_scalar"]: 
            return False 
        if chro_interval not in LegalIntervalsFifthSpecies["adjacent_melodic_chromatic"]: 
            return False 
        if (sdg_interval, chro_interval) in LegalIntervalsFifthSpecies["forbidden_combinations"]: 
            return False 
        if abs(sdg_interval) >= 5 and (self._mr[line].is_sharp(self._counterpoint_lst[line][-1]) or self._mr[line].is_sharp(note)):
            return False
        return True 

    def _handles_interval_order(self, note: Note, index: tuple, line: int) -> bool:
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
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
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
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
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
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
        if self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
        return self._counterpoint_lst[line][-1].get_scale_degree_interval(note) == -2

    def _handles_repeated_two_notes(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if len(self._counterpoint_lst[line]) < 3: return True 
        if self._counterpoint_lst[line][-3].get_accidental() == ScaleOption.REST: return True
        if not self._mr[line].is_unison(self._counterpoint_lst[line][-3], self._counterpoint_lst[line][-1]) or not self._mr[line].is_unison(self._counterpoint_lst[line][-2], note):
            return True 
        if self._counterpoint_lst[line][-1].get_scale_degree_interval(note) != 2: return False 
        if self._counterpoint_lst[line][-2].get_duration() != 8 or beat != 0: return False 
        return True

    def _handles_quarter_between_two_leaps(self, note: Note, index: tuple, line: int) -> bool:
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
        if self._counterpoint_lst[line][-1].get_duration() != 2 or len(self._counterpoint_lst[line]) < 2: return True 
        first_interval, second_interval = self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1]), self._counterpoint_lst[line][-1].get_scale_degree_interval(note)
        if abs(first_interval) == 2 or abs(second_interval) == 2:
            return True 
        if first_interval > 0 and second_interval < 0: return False 
        if first_interval == -8 and second_interval == 8: return False 
        return True 

    def _handles_upper_neighbor(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
        if len(self._counterpoint_lst[line]) >= 2 and self._counterpoint_lst[line][-2].get_accidental() == ScaleOption.REST: return True
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

    def _handles_final_unsyncopated_whole_note(self, note: Note, index: tuple, line: int) -> bool:
        if index != (self._length - 2, 0): return True 
        final, sdg = self._mr[line].get_final(), note.get_scale_degree()
        if sdg - 1 == final: return note.get_accidental() == ScaleOption.NATURAL
        if sdg < final: sdg += 7
        if self._get_counterpoint_note(index, line) is not None and note.get_scale_degree_interval(self._get_counterpoint_note(index, line)) < 0: return False
        if sdg - 4 == final: return note.get_accidental() == ScaleOption.NATURAL
        return False 

    def _handles_contrary_motion_surrounding_quarter_note_octave_leap(self, note: Note, index: tuple, line: int) -> bool:
        if len(self._counterpoint_lst[line]) < 2 or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
        if self._counterpoint_lst[line][-1].get_duration() != 2: return True 
        prev_interval, cur_interval = self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1]), self._counterpoint_lst[line][-1].get_scale_degree_interval(note)
        if prev_interval < 0 and cur_interval == -8: return False 
        if prev_interval == 8 and cur_interval > 0: return False 
        return True 

    def _handles_final_leading_tone(self, note: Note, index: tuple, line: int) -> bool:
        if index != (self._length - 2, 2): return True 
        final = self._mr[line].get_final() 
        if (note.get_scale_degree() + 1) % 7 != final: return True 
        if (final in [2, 5, 6] and note.get_accidental() != ScaleOption.SHARP) or (final in [1, 3, 4] and note.get_accidental() != ScaleOption.NATURAL):
            return False 
        return True 

    def _handles_preset_suspension_resolution(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if beat not in [1, 2]: return True 
        if (bar, 0) not in self._attempt_params[line]["suspension_indices"]: return True 
        susp_note = self._counterpoint_obj[line][(bar - 1, 2)] if (bar - 1, 2) in self._counterpoint_obj[line] else self._counterpoint_obj[line][(bar - 1, 0)]
        if susp_note.get_scale_degree_interval(note) != -2: return False 
        return True

    ######################################
    ###### harmonic insertion checks ######

    def _filters_dissonance_on_downbeat(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2 
        if beat % 2 != 0 or (bar, beat) not in self._counterpoint_obj[other_line]: return True 
        c_note = self._counterpoint_obj[other_line][(bar, beat)]
        if c_note is not None and not self._is_consonant(c_note, note): 
            return False 
        return True 
        
    def _resolves_suspension(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if beat not in [1, 2] or (bar, 0) in self._counterpoint_obj[line]: return True 
        susp_index = (bar - 1, 2) if (bar - 1, 2) in self._counterpoint_obj[line] else (bar - 1, 0)
        c_note, susp = self._get_counterpoint_note((bar, 0), line), self._counterpoint_obj[line][susp_index]
        if c_note is not None and c_note.get_scale_degree_interval(susp) in LegalIntervalsFifthSpecies["resolvable_dissonance"]:
            if susp.get_scale_degree_interval(note) != -2: return False 
            if beat == 1: return True 
            if self._get_counterpoint_note(index, line) is None: return True 
            return self._is_consonant(self._get_counterpoint_note(index, line), note)
        return True 

    def _forms_suspension(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        if beat != 0 or (bar, 0) in self._counterpoint_obj[other_line] or self._get_counterpoint_note(index, line) is None:
            return True 
        c_note = self._get_counterpoint_note(index, line)
        #Note: pay attention to order.  
        if self._is_consonant(c_note, note): return True 
        if note.get_scale_degree_interval(c_note) in LegalIntervalsFifthSpecies["resolvable_dissonance"]:
            for index_to_check in [(bar, 1), (bar, 2)]:
                if index_to_check in self._counterpoint_obj[other_line]:
                    should_resolve = self._counterpoint_obj[other_line][index_to_check]
                    if should_resolve is not None and c_note.get_scale_degree_interval(should_resolve) != -2: return False
            return True 
        return False 


    def _prepares_weak_quarter_dissonance(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        c_note = self._get_counterpoint_note(index, line) 
        if beat % 2 != 1 or c_note is None or self._is_consonant(c_note, note): return True 
        if not self._is_consonant(self._get_counterpoint_note((bar, beat - 1), line), self._counterpoint_lst[line][-1]): return False 
        if index in self._counterpoint_obj[other_line]:
            c_prev = self._get_counterpoint_note((bar, beat - 1), line)
            c_next_index = (bar + 1, 0) if beat == 3 else (bar, 2)
            c_next = self._counterpoint_obj[other_line][c_next_index] if c_next_index in self._counterpoint_obj[other_line] else None
            if c_note is None or c_prev is None or c_next is None: return True
            first_intvl, second_intvl = c_prev.get_scale_degree_interval(c_note), c_note.get_scale_degree_interval(c_next)
            if (first_intvl, second_intvl) not in [(-2, -2), (2, 2), (2, -2), (-2, 2), (-2, -3)]: return False
            if (first_intvl, second_intvl) == (-2, 3):
                index_plus_two = (bar, 3) if beat == 1 else (bar + 1, 1)
                index_plus_three = (bar + 1, 0) if beat == 1 else (bar + 1, 2)
                if index_plus_three not in self._counterpoint_obj[other_line]: return False 
                else:
                    cambiata_tail_end = self._counterpoint_obj[other_line][index_plus_three]
                    if index_plus_two in self._counterpoint_obj[other_line]:
                        if c_next.get_scale_degree_interval(self._counterpoint_obj[other_line][index_plus_two]) != 2: return False 
                        if self._counterpoint_obj[other_line][index_plus_two].get_scale_degree_interval(self._counterpoint_obj[other_line][index_plus_three]) != 2: return False 
                    elif c_next.get_scale_degree_interval(self._counterpoint_obj[other_line][index_plus_three]) != 2: return False
        return abs(self._counterpoint_lst[line][-1].get_scale_degree_interval(note)) == 2

    def _resolves_weak_quarter_dissonance(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
        if beat % 2 != 0 or self._counterpoint_lst[line][-1].get_duration() != 2: return True 
        index_to_check = (bar, 1) if beat == 2 else (bar - 1, 3)
        c_note = self._get_counterpoint_note(index_to_check, line)
        if c_note is None or self._is_consonant(c_note, self._counterpoint_lst[line][-1]): return True 
        first_interval = self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1])
        second_interval = self._counterpoint_lst[line][-1].get_scale_degree_interval(note) 
        if second_interval not in [-3, -2, 2]: return False 
        if first_interval == 2 and second_interval == -3: return False 
        return True 

    def _resolves_cambiata_tail(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if beat == 1.5: return True 
        first_index, second_index = (bar - 1, 1), (bar - 1, 2)
        if beat in [1, 2]:
            first_index, second_index = (bar - 1, 3), (bar, 0)
        if beat == 3:
            first_index, second_index = (bar , 1), (bar, 2)
        if first_index not in self._counterpoint_obj[line] or second_index not in self._counterpoint_obj[line]: return True 
        c_note = self._get_counterpoint_note(first_index, line)
        if c_note is not None and not self._is_consonant(c_note, self._counterpoint_obj[line][first_index]) and self._counterpoint_obj[line][first_index].get_scale_degree_interval(self._counterpoint_obj[line][second_index]) == -3:
            return self._counterpoint_lst[line][-1].get_scale_degree_interval(note) == 2
        return True 

    def _prepares_weak_half_note(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if beat != 2: return True 
        c_note = self._get_counterpoint_note(index, line)
        if c_note is None or self._is_consonant(c_note, note): return True 
        if (bar, 0) not in self._counterpoint_obj[line] or self._counterpoint_obj[line][(bar, 0)].get_duration() != 4: return False 
        return abs(self._counterpoint_obj[line][(bar, 0)].get_scale_degree_interval(note)) == 2

    def _resolves_dissonant_quarter_on_weak_half_note(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if beat != 3 or (bar, 2) not in self._counterpoint_obj[line]: return True 
        c_note = self._get_counterpoint_note((bar, beat - 1), line)
        if c_note is None or self._is_consonant(c_note, self._counterpoint_obj[line][(bar, 2)]): return True 
        return self._counterpoint_obj[line][(bar, 2)].get_scale_degree_interval(note) == -2

    def _resolves_passing_half_note(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat) = index
        if beat != 0 or (bar - 1, 2) not in self._counterpoint_obj[line] or self._counterpoint_obj[line][(bar - 1, 2)].get_duration() != 4: return True 
        c_note = self._get_counterpoint_note((bar - 1, 2), line)
        if c_note is None or self._is_consonant(self._counterpoint_obj[line][(bar - 1, 2)], c_note): return True 
        return self._counterpoint_lst[line][-2].get_scale_degree_interval(self._counterpoint_lst[line][-1]) == self._counterpoint_lst[line][-1].get_scale_degree_interval(note)

    def _handles_hiddens(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
        if index not in self._counterpoint_obj[other_line]: return True 
        c_note = self._counterpoint_obj[other_line][index]
        if c_note is None or c_note.get_chromatic_interval(note) not in [-19, -12, -7, 0, 7, 12, 19]: return True 
        upper_interval = self._counterpoint_lst[line][-1].get_scale_degree_interval(note)
        lower_interval = self._get_counterpoint_note((bar, beat - 1) if beat != 0 else (bar - 1, 3), line).get_scale_degree_interval(c_note)
        if (upper_interval > 0 and lower_interval > 0) or (upper_interval < 0 and lower_interval < 0): return False 
        return True 

    def _handles_parallels(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        c_note = self._get_counterpoint_note(index, line)
        if c_note is None: return True
        intvl = c_note.get_chromatic_interval(note)
        if intvl not in [-19, -12, 0, 12, 19]: return True 
        prev_beat_index = (bar, beat - 1) if beat != 0 else (bar - 1, 3)
        if self._get_counterpoint_note(prev_beat_index, line) is not None and self._get_counterpoint_note(prev_beat_index, line).get_chromatic_interval(self._counterpoint_lst[line][-1]) == intvl:
            if not self._mr[line].is_unison(self._counterpoint_lst[line][-1], note): return False 
        if beat % 2 != 0: return True 
        prev_half_note_index = (bar, 0) if beat == 2 else (bar - 1, 2)
        c_prev_half = self._get_counterpoint_note(prev_half_note_index, line)
        if c_prev_half is not None and c_prev_half.get_chromatic_interval(self._get_counterpoint_note(prev_half_note_index, other_line)) == intvl:
            return False 
        if (bar - 1, beat) in self._counterpoint_obj[line] and self._counterpoint_obj[line][(bar - 1, beat)].get_duration() == 2: return True 
        if (bar - 1, beat) in self._counterpoint_obj[other_line] and self._counterpoint_obj[other_line][(bar - 1, beat)] is not None and self._counterpoint_obj[other_line][(bar - 1, beat)].get_duration() == 2: return True 
        c_prev_whole = self._get_counterpoint_note((bar - 1, beat), line)
        if c_prev_whole is not None and c_prev_whole.get_chromatic_interval(self._get_counterpoint_note((bar - 1, beat), other_line)) == intvl:
            return False 
        return True 

    def _handles_doubled_leading_tone(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        if beat % 2 != 0 or (beat == 2 and (index not in self._counterpoint_obj[other_line] or self._counterpoint_obj[other_line][index])):
            return True 
        c_note = self._get_counterpoint_note(index, line)
        if c_note is None or c_note.get_chromatic_interval(note) not in [-12, 0, 12]: return True 
        if (note.get_scale_degree() + 1) % 7 == self._mr[line].get_final(): return False 
        return True 

    def _no_vertical_cross_relations(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        c_note = self._get_counterpoint_note(index, line)
        if c_note is not None and c_note.get_scale_degree() == note.get_scale_degree() and c_note.get_accidental() != note.get_accidental():
            return False 
        return True 

    def _no_diagonal_cross_relations(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        if beat == 1.5: return True
        prev_index = (bar, beat - 1) if beat != 0 else (bar - 1, 3)
        c_note = self._get_counterpoint_note(prev_index, line)
        if c_note is not None and c_note.get_scale_degree() == note.get_scale_degree() and c_note.get_chromatic_interval(note) % 12 != 0: 
            return False 
        return True

    def _prevents_suspensions_from_resolving_to_perfect_intervals(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        if beat != 2: return True 
        c_note = self._counterpoint_obj[other_line][index] if index in self._counterpoint_obj[other_line] else None 
        if c_note is None or abs(c_note.get_scale_degree_interval(note)) % 7 not in [1, 5]: return True 
        note1, note2 = self._get_counterpoint_note((bar, 0), line), self._get_counterpoint_note((bar, 0), other_line)
        if note1.get_scale_degree_interval(note2) in LegalIntervalsFifthSpecies["resolvable_dissonance"]: return False 
        if note2.get_scale_degree_interval(note1) in LegalIntervalsFifthSpecies["resolvable_dissonance"]: return False 
        return True

    def _sharp_moves_up_if_against_tritone(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
        if self._mr[line].is_sharp(self._counterpoint_lst[line][-1]):
            c_note = self._get_counterpoint_note((bar, beat - 1) if beat != 0 else (bar - 1, 3), line)
            if c_note is not None and abs(c_note.get_chromatic_interval(note)) % 12 == 6:
                return self._counterpoint_lst[line][-1].get_scale_degree_interval(note) == 2
        return True

    def _handles_landini(self, note: Note, index: tuple, line: int) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return True
        if beat % 2 != 0: return True 
        if self._mr[line].is_sharp(self._counterpoint_lst[line][-1]) and index in self._counterpoint_obj[other_line]:
            c_note = self._counterpoint_obj[other_line][index]
            if c_note is not None and abs(c_note.get_chromatic_interval(self._counterpoint_lst[line][-1])) % 12 == 6:
                if self._counterpoint_lst[line][-1].get_chromatic_interval(note) == 1: return False 
        return True


    ######################################
    ###### melodic rhythms filters #######

    def _get_durations_from_beat(self, index: tuple) -> set:
        (bar, beat) = index
        if beat == 1.5: return { 1 }
        if beat == 3: return { 2 }
        if beat == 1: return { 1, 2 }
        if beat == 2: return { 2, 4, 6, 8 }
        if beat == 0: return { 2, 4, 6, 8, 12, 16 }

    def _handles_consecutive_quarters(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return durs
        if self._counterpoint_lst[line][-1].get_duration() != 2: return durs 
        if self._counterpoint_lst[line][-1].get_scale_degree_interval(note) > 0 and beat == 2: durs.discard(4)
        if beat == 2 and self._counterpoint_lst[line][-2].get_duration() == 2 and self._counterpoint_lst[line][-1].get_duration() == 2 and self._counterpoint_lst[line][-3].get_duration() != 2:
            durs.discard(4)
        for i in range(len(self._counterpoint_lst[line]) - 2, -1, -1):
            if self._counterpoint_lst[line][i].get_duration() != 2:
                return durs 
            if abs(self._counterpoint_lst[line][i].get_scale_degree_interval(self._counterpoint_lst[line][i + 1])) > 2:
                durs.discard(2)
                return durs 
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
            durs.discard(2)
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

    def _handles_double_syncopation(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat), other_line = index, (line + 1) % 2
        if beat == 0 and (bar + 1, 0) not in self._counterpoint_obj[other_line]:
            durs.discard(12)
        if beat == 2 and (bar + 1, 0) not in self._counterpoint_obj[other_line]:
            durs.discard(8)
            durs.discard(6)
        return durs 

    def _handles_repeated_note(self, note: Note, index: tuple, line: int, durs: set) -> set:
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return durs
        if self._mr[line].is_unison(self._counterpoint_lst[line][-1], note): 
            durs.discard(4)
            durs.discard(2)
        return durs

    def _handles_rhythm_after_descending_quarter_leap(self, note: Note, index: tuple, line: int, durs: set) -> set:
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return durs
        (bar, beat) = index
        if self._counterpoint_lst[line][-1].get_duration() == 2 and self._counterpoint_lst[line][-1].get_scale_degree_interval(note) < -2:
            durs.discard(8)
            durs.discard(12)
            durs.discard(6)
        return durs

    def _handles_dotted_whole_after_quarters(self, note: Note, index: tuple, line: int, durs: set) -> set:
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return durs
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
        other_line = (line + 1) % 2
        if index == (self._length - 3, 2): 
            if (self._length - 2, 0) in self._counterpoint_obj[other_line] and self._counterpoint_obj[other_line][(self._length - 2, 0)] is not None:
                if note.get_scale_degree() != self._mr[line].get_final(): return set()
                durs.discard(4)
                durs.discard(2)
            if (self._length - 2, 0) not in self._counterpoint_obj[other_line]:
                durs.discard(8)
                durs.discard(6)
        if index == (self._length - 3, 0) and (self._length - 2, 0) in self._counterpoint_obj[other_line] and self._counterpoint_obj[other_line][(self._length - 2, 0)] is not None:
            durs.discard(6)
            durs.discard(8) 
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
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return durs
        if beat == 0 and self._counterpoint_lst[line][-1].get_duration() == 8:
            durs.discard(2)
        return durs
        
    def _handles_repetition_on_consecutive_syncopated_measures(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat), other_line = index, (line + 1) % 2
        if beat == 2 and (bar, 0) not in self._counterpoint_obj[line] and (bar - 1, 2) in self._counterpoint_obj[line] and self._mr[line].is_unison(self._counterpoint_obj[line][(bar - 1, 2)], note):
            durs.discard(6)
            durs.discard(8)
        return durs

    def _prepares_preset_suspension_rhythmically(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat), other_line = index, (line + 1) % 2
        if (bar + 1, 0) in self._attempt_params[line]["suspension_indices"]:
            if beat == 0:
                durs.discard(6)
                durs.discard(8)
            if beat == 2:
                durs.discard(2)
                durs.discard(4)
        if (bar + 1, 0) in self._attempt_params[other_line]["suspension_indices"]:
            if beat == 0:
                durs.discard(12)
            if beat == 2:
                durs.discard(6)
                durs.discard(8)
        return durs 



    ##########################################
    ###### harmonic rhythm filters ###########

    def _get_first_beat_options(self, note: Note, line: int) -> set:
        other_line = (line + 1) % 2
        durs = { 4, 6, 8, 12 }
        if (1, 0) not in self._counterpoint_obj[other_line]: durs.discard(12)
        return durs

    def _prepares_suspension(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index 
        if bar == self._length - 1 or self._get_counterpoint_note((bar + 1, 0), line) is None or self._is_consonant(self._get_counterpoint_note((bar + 1, 0), line), note): 
            return durs 
        if self._get_counterpoint_note((bar + 1, 0), line).get_scale_degree_interval(note) in LegalIntervalsFifthSpecies["resolvable_dissonance"]:
            return durs 
        if beat == 0:
            durs.discard(12)
        if beat == 2:
            durs.discard(8)
            durs.discard(6)
        return durs 

    def _resolves_cambiata(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index 
        if beat % 2 != 0: return durs 
        index_to_check = (bar - 1, 3) if beat == 0 else (bar, 1)
        if index_to_check not in self._counterpoint_obj[line]: return durs 
        c_note = self._get_counterpoint_note(index_to_check, line)
        if c_note is None or self._is_consonant(c_note, self._counterpoint_obj[line][index_to_check]): return durs 
        if self._counterpoint_obj[line][index_to_check].get_scale_degree_interval(note) != -3: return durs 
        durs.discard(12)
        durs.discard(8)
        durs.discard(6)
        return durs 

    def _handles_weak_half_note_dissonance(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index 
        if beat != 2: return durs
        c_note = self._get_counterpoint_note(index, line)
        if c_note is None or self._is_consonant(c_note, note): return durs 
        durs.discard(6)
        durs.discard(8)
        if index == (0, 0) or self._counterpoint_lst[line][-1].get_accidental() == ScaleOption.REST: return durs
        if self._counterpoint_lst[line][-1].get_scale_degree_interval(note) == 2:
            durs.discard(2)
        return durs

    def _forms_weak_quarter_dissonance(self, note: Note, index: tuple, line: int, durs: set) -> bool:
        (bar, beat), other_line = index, (line + 1) % 2
        if beat % 2 != 0: return durs 
        indices_to_check = [(bar, 1), (bar, 3), (bar + 1, 1)] if beat == 0 else [(bar, 3), (bar + 1, 1)]
        for i, index_to_check in enumerate(indices_to_check):
            is_handled = True
            (bar_to_check, beat_to_check) = index_to_check
            c_note = self._counterpoint_obj[other_line][index_to_check] if index_to_check in self._counterpoint_obj[other_line] else None 
            if c_note is not None and not self._is_consonant(c_note, note):
                if abs(self._get_counterpoint_note((bar_to_check, beat_to_check - 1), line).get_scale_degree_interval(c_note)) != 2:
                    is_handled = False
                next_index = (bar_to_check, beat_to_check + 1) if beat_to_check != 3 else (bar_to_check + 1, 0)
                after_dis = self._counterpoint_obj[other_line][next_index] if next_index in self._counterpoint_obj[other_line] else None 
                if after_dis is not None:
                    if c_note.get_scale_degree_interval(after_dis) not in [-3, -2, 2]: is_handled = False 
                    if c_note.get_scale_degree_interval(after_dis) == -3:
                        if after_dis.get_duration() not in [2, 4]: is_handled = False
                        tail_note2 = self._counterpoint_obj[other_line][(bar_to_check + 1, beat_to_check - 1)] if (bar_to_check + 1, beat_to_check - 1) in self._counterpoint_obj[other_line] else None
                        if after_dis.get_duration() == 4 and tail_note2 is not None and after_dis.get_scale_degree_interval(tail_note2) != 2: is_handled = False
                        if after_dis.get_duration() == 2:
                            tail_note1_index = (bar_to_check, 3) if beat_to_check == 1 else (bar_to_check + 1, 1)
                            tail_note1 = self._counterpoint_obj[other_line][tail_note1_index] if tail_note1_index in self._counterpoint_obj[other_line] else None
                            if tail_note1 is not None:
                                if after_dis.get_scale_degree_interval(tail_note1) != 2: is_handled = False
                                if tail_note2 is not None and tail_note1.get_scale_degree_interval(tail_note2) != 2: is_handled = False
            if not is_handled:
                if i == 2: 
                    durs.discard(12)
                if i == 1:
                    durs.discard(12)
                    durs.discard(8)
                if i == 0:
                    durs.discard(12)
                    durs.discard(8)
                    durs.discard(6)
                    durs.discard(4)
        return durs

    def _forms_weak_half_note_dissonance(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat), other_line = index, (line + 1) % 2
        if beat != 0: return durs 
        c_note = self._counterpoint_obj[other_line][(bar, 2)] if (bar, 2) in self._counterpoint_obj[other_line] else None 
        if c_note is None or self._is_consonant(c_note, note): return durs 
        is_handled = True 
        if not self._is_consonant(self._get_counterpoint_note((index), line), note): is_handled = False
        else:
            c_prev = self._get_counterpoint_note((bar, 1), line)
            if abs(c_prev.get_scale_degree_interval(c_note)) != 2 or c_note.get_duration() > 4:
                is_handled = False 
            elif c_note.get_duration() == 2:
                if c_prev.get_scale_degree_interval(c_note) != -2: is_handled = False 
                else:
                    c_next = self._counterpoint_obj[other_line][(bar, 3)]
                    if c_next is not None and c_note.get_scale_degree_interval(c_next) != -2: is_handled = False 
                    if c_next is not None and not self._is_consonant(c_next, note):
                        durs.discard(12)
                        durs.discard(8)
            else:
                c_next = self._counterpoint_obj[other_line][(bar + 1, 0)] if (bar + 1, 0) in self._counterpoint_obj[other_line] else None
                if c_next is not None and not self._is_consonant(c_next, note):
                    durs.discard(12)
                if c_next is not None and c_note.get_scale_degree_interval(c_next) != c_prev.get_scale_degree_interval(c_note):
                    is_handled = False 
        if not is_handled:
            durs.discard(12)
            durs.discard(8)
            durs.discard(6)
        return durs 

    def _doesnt_create_dissonance_on_following_measure(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index
        if beat != 0: return durs 
        c_note = self._get_counterpoint_note((bar + 1, 2), line)
        if c_note is not None and not self._is_consonant(c_note, note): durs.discard(16)
        if (bar + 1, 0) not in self._counterpoint_obj[0] or self._is_consonant(self._counterpoint_obj[0][(bar + 1, 0)], note): return durs 
        durs.discard(16)
        if (bar + 1, 0) in self._counterpoint_obj[0] and self._counterpoint_obj[0][(bar + 1, 0)].get_scale_degree_interval(note) not in LegalIntervalsFifthSpecies["resolvable_dissonance"]:
            durs.discard(12)
        return durs

    def _doesnt_create_dissonance_on_next_half_note(self, note: Note, index: tuple, line: int, durs: set) -> set:
        (bar, beat) = index
        if beat != 0: return durs 
        c_note = self._counterpoint_obj[0][(bar, 2)] if (bar, 2) in self._counterpoint_obj[0] else None 
        if c_note is None or self._is_consonant(c_note, note): return durs 
        if c_note.get_duration() > 4: return set()
        if self._get_counterpoint_note(index, line).get_scale_degree_interval(c_note) not in [-2, 2]: return set()
        c_next = self._counterpoint_obj[0][(bar + 1, 0)] if (bar + 1, 0) in self._counterpoint_obj[0] else None 
        if c_next is not None and c_note.get_scale_degree_interval(note) != self._get_counterpoint_note(index, line).get_scale_degree_interval(c_note):
            return durs
        if c_next is not None and not self._is_consonant(c_next, note):
            durs.discard(12)
            durs.discard(16)
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

    def _increment_theme_index(self, note: Note, index: tuple, line: int) -> None:
        if note.get_accidental() != ScaleOption.REST:
            self._attempt_params[line]["theme_index"] += 1

    ##########################################
    ########### final checks #################

    def _parameters_are_correct(self) -> bool:
        # print("num runs placed:", self._attempt_params["num_runs_placed"])
        # print("max run has been placed?", self._attempt_params["max_quarter_run_has_been_placed"])
        return self._attempt_params["num_runs_placed"] >= self._attempt_params["min_runs_of_length_4_or_more"] and self._attempt_params["max_quarter_run_has_been_placed"]

    def _has_only_two_octaves(self) -> bool:
        for line in range(2):
            num_octaves = 0
            for i in range(0 if self._counterpoint_lst[line][0].get_accidental() != ScaleOption.REST else 1, len(self._counterpoint_lst[line]) - 1):
                if abs(self._counterpoint_lst[line][i].get_scale_degree_interval(self._counterpoint_lst[line][i + 1])) == 8:
                    num_octaves += 1
                    max_octaves = 1 if self._length < 10 else 2
                    if num_octaves > max_octaves: 
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
                            if not resolved: 
                                return False 
        return True 

    def _top_line_resolves_by_step(self) -> bool:
        top_line = 1 if self._counterpoint_lst[0][-1].get_chromatic_interval(self._counterpoint_lst[1][-1]) >= 0 else 0
        return abs(self._counterpoint_lst[top_line][-2].get_scale_degree_interval(self._counterpoint_lst[top_line][-1])) == 2


    ##########################################
    ########### scoring ######################

    def _score_solution(self, solution: list[list[Note]]) -> int:
        score = 0
        theme_measures = 0
        for note in solution[0]: theme_measures += note.get_duration() / 8
        rest_measures = 0
        for note in solution[1]:
            if note.get_accidental() == ScaleOption.REST:
                rest_measures += 1
            else: break
        score -= (theme_measures - rest_measures) * 10
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
        (sdg_interval, chro_interval) = self._mr[0].get_intervals(note1, note2)
        if sdg_interval not in LegalIntervalsFifthSpecies["harmonic_scalar"]: return False 
        if chro_interval not in LegalIntervalsFifthSpecies["harmonic_chromatic"]: return False 
        if (sdg_interval, chro_interval) in LegalIntervalsFifthSpecies["forbidden_combinations"]: return False 
        if self._mr[0].is_sharp(note1) and self._mr[0].is_sharp(note2): return False
        return True 

    def _get_counterpoint_note(self, index: tuple, line: int) -> Note:
        (bar, beat), other_line = index, (line + 1) % 2
        total_beats_traversed = 0
        while (bar, beat) not in self._counterpoint_obj[other_line]:
            beat -= 0.5 
            total_beats_traversed += 0.5
            if beat < 0:
                beat += 4
                bar -= 1
            if bar < 0: 
                return None
        note = self._counterpoint_obj[other_line][(bar, beat)]
        if note is None or note.get_duration() / 2 <= total_beats_traversed: return None
        return note