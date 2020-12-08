from random import random, shuffle, randint
import math
from time import time

from notation_system import ModeOption, ScaleOption, RangeOption, Note, ModeResolver 
from cantus_firmus import CantusFirmus, GenerateCantusFirmus
from two_part_first_species import Orientation
from legal_intervals import LegalIntervalsFifthSpecies, MaxAcceptableRepetitions

class GenerateTwoPartFifthSpecies:

    def __init__(self, length: int = None, mode: ModeOption = None, range_option: RangeOption = None):
        self._mode = mode or ModeOption.AEOLIAN
        self._length = length or 8 + math.floor(random() * 5) #todo: replace with normal distribution
        self._range = range_option if range_option is not None else RangeOption.ALTO
        self._mr = ModeResolver(self._mode, range_option=self._range)
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
        self._rhythm_filters = [
            self._handles_consecutive_quarters,
            self._handles_penultimate_bar,
            self._handles_first_eighth,
            self._handles_sharp_durations,
            self._handles_whole_note_quota,
            self._handles_repeated_note,
            self._handles_rhythm_after_descending_quarter_leap,
            self._handles_dotted_whole_after_quarters,
            self._handles_repeated_dotted_halfs,
            self._handles_antipenultimate_rhythm
        ]
        self._index_checks = [
            self._highest_and_lowest_placed
        ]
        self._change_params = [
            self._check_for_highest_and_lowest,
            self._check_for_on_beat_whole_note,
            self._check_if_new_run_is_added,
            self._check_if_eighths_are_added
        ]
        self._final_checks = [
            self._parameters_are_correct,
            self._has_only_one_octave
        ]
        self._params = [
            "highest_has_been_placed", "lowest_has_been_placed",
            "max_quarter_run_has_been_placed", "num_runs_placed",
            "num_on_beat_whole_notes_placed", "eighths_have_been_placed"
        ]
        gcf = GenerateCantusFirmus(self._length, self._mode, 4)
        cf = None 
        #limit ourselves to Cantus Firmuses that end with a descending step to allow for easier cadences
        while cf is None or cf.get_note(self._length - 2).get_scale_degree_interval(cf.get_note(self._length - 1)) != -2:
            cf = gcf.generate_cf()
        self._cantus_object = cf
        self._cantus = cf.get_notes()

    def print_counterpoint(self):
        print("  FIFTH SPECIES:")
        for i in range(self._length):
            for j in range(4):
                cntpt_note = str(self._counterpoint_obj[(i, j)]) if (i, j) in self._counterpoint_obj else ""
                if cntpt_note is None: cntpt_note = "None"
                if (i, j + 0.5) in self._counterpoint_obj: cntpt_note += "  " + str(self._counterpoint_obj[(i, j + 0.5)])
                show_index = "    "
                if j == 0:
                    show_index = str(i) + ":  " if i < 10 else str(i) + ": "
                print(show_index + "   " + str(cntpt_note))

    def get_optimal(self):
        if len(self._solutions) == 0:
            return None 
        optimal = self._solutions[0]
        self._map_solution_onto_counterpoint_dict(optimal)
        self.print_counterpoint()
        return [optimal, self._cantus]

    def generate_2p5s(self):
        print("MODE = ", self._mode.value["name"])
        self._solutions = []
        def attempt():
            self._num_backtracks = 0
            self._solutions_this_attempt = 0
            initialized = self._initialize()
            self._backtrack()
        attempts = 0
        while len(self._solutions) < 100 and attempts < 1:
            print("attempt", attempts)
            attempt()
            attempts += 1
        print("number of attempts:", attempts)
        print("number of solutions:", len(self._solutions))
        if len(self._solutions) > 0:
            shuffle(self._solutions)
            self._solutions.sort(key = lambda sol: self._score_solution(sol)) 

    def _initialize(self) -> bool:
        indices = []
        for i in range(self._length - 1):
            indices += [(i, 0), (i, 1), (i, 1.5), (i, 2), (i, 3)]
        indices += [(self._length - 1, 0)]
        self._all_indices = indices[:]
        self._remaining_indices = indices[:]
        self._remaining_indices.reverse()
        #initialize counterpoint data structure, that will map indices to notes
        self._counterpoint_obj = {}
        for index in self._all_indices: self._counterpoint_obj[index] = None 
        #also initialize counterpoint data structure as list 
        self._counterpoint_lst = []
        #initialize parameters for this attempt
        self._attempt_params = {
            "lowest": None, "highest": None, "highest_must_appear_by": None, "lowest_must_appear_by": None, 
            "highest_has_been_placed": False, "lowest_has_been_placed": False,
            "min_length_of_max_quarter_run": None, "max_quarter_run_has_been_placed": False,
            "min_runs_of_length_4_or_more": None, "num_runs_placed": 0,
            "max_on_beat_whole_notes": None, "num_on_beat_whole_notes_placed": 0,
            "eighths_have_been_placed": False
        }
        vocal_range = randint(8, 10)
        self._attempt_params["lowest"] = self._mr.get_default_note_from_interval(self._mr.get_lowest(), randint(1, 13 - vocal_range))
        self._attempt_params["highest"] = self._mr.get_default_note_from_interval(self._attempt_params["lowest"], vocal_range)
        self._attempt_params["highest_must_appear_by"] = randint(3, self._length - 1)
        self._attempt_params["lowest_must_appear_by"] = randint(3 if self._attempt_params["highest_must_appear_by"] >= 5 else 5, self._length - 1)
        self._attempt_params["min_length_of_max_quarter_run"] = randint(5, 10)
        self._attempt_params["min_runs_of_length_4_or_more"] = randint(1, 2)
        self._attempt_params["max_on_beat_whole_notes"] = randint(1, 2)
        self._store_params = []
        self._stored_indices = []
        # print("min runs of length 4 or more:")
        # print(self._attempt_params["min_runs_of_length_4_or_more"])
        # print("min length of max quarter run")
        # print(self._attempt_params["min_length_of_max_quarter_run"])
        self._valid_pitches = [self._attempt_params["lowest"], self._attempt_params["highest"]] #order is unimportant
        for i in range(2, vocal_range):
            self._valid_pitches += self._mr.get_notes_from_interval(self._attempt_params["lowest"], i)
        
        return True 

    def _backtrack(self) -> None:
        if (self._solutions_this_attempt > 500 or self._num_backtracks > 50000) or (self._solutions_this_attempt == 0 and self._num_backtracks > 20000):
            return 
        self._num_backtracks += 1
        if self._num_backtracks % 10000 == 0:
            print("backtrack number:", self._num_backtracks)
        if len(self._remaining_indices) == 0:
            if self._passes_final_checks():
                if self._solutions_this_attempt == 0:
                    print("FOUND SOLUTION!")
                self._solutions.append(self._counterpoint_lst[:])
                self._solutions_this_attempt += 1
            return 
        (bar, beat) = self._remaining_indices.pop() 
        if self._passes_index_checks((bar, beat)):
            candidates = list(filter(lambda n: self._passes_insertion_checks(n, (bar, beat)), self._valid_pitches))
            shuffle(candidates)
            if bar == 0 and beat == 0: candidates.append(Note(1, 0, 4, accidental=ScaleOption.REST))
            # print("candidates for index", bar, beat, ": ", len(candidates))
            notes_to_insert = []
            for candidate in candidates: 
                durations = self._get_valid_durations(candidate, (bar, beat))
                for dur in durations:
                    if dur in [2, 6, 4, 8, 12, 1, 16]:
                        notes_to_insert.append(Note(candidate.get_scale_degree(), candidate.get_octave(), dur, accidental=candidate.get_accidental()))
            shuffle(notes_to_insert)
            for note_to_insert in notes_to_insert:
                self._insert_note(note_to_insert, (bar, beat))
                self._backtrack()
                self._remove_note(note_to_insert, (bar, beat))
        self._remaining_indices.append((bar, beat))

    def _passes_index_checks(self, index: tuple) -> bool:
        for check in self._index_checks:
            if not check(index): return False 
        return True

    def _passes_insertion_checks(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index 
        if bar == 0 and (beat == 0 or (beat == 2 and self._counterpoint_lst[0].get_accidental() == ScaleOption.REST)):
            return self._check_starting_pitch(note)
        if bar == self._length - 1:
            if not self._check_last_pitch(note): return False
        for check in self._melodic_insertion_checks:
            if not check(note, (bar, beat)): 
                # print("failed insertion check:", str(note), index, "on function", check.__name__)
                return False 
        # print("passed insertion checks!", str(note), index)
        return True 

    def _get_valid_durations(self, note: Note, index: tuple) -> set:
        (bar, beat) = index 
        if bar == self._length - 1: return { 16 }
        if note.get_accidental() == ScaleOption.REST: return { 4 }
        if bar == 0 and beat == 0: return { 12, 8, 6, 4 }
        durs = self._get_durations_from_beat(beat)
        prev_length = len(durs)
        for check in self._rhythm_filters:
            durs = check(note, index, durs)
            if len(durs) == 0: break
        return durs 

    def _insert_note(self, note: Note, index: tuple) -> set:
        self._counterpoint_lst.append(note)
        self._counterpoint_obj[index] = note
        self._store_params.append({})
        for param in self._params:
            self._store_params[-1][param] = self._attempt_params[param]
        self._bury_indices(note, index)
        for check in self._change_params:
            check(note, index)

    def _remove_note(self, note: Note, index: tuple) -> set:
        self._counterpoint_lst.pop()
        self._counterpoint_obj[index] = None
        for param in self._params:
            self._attempt_params[param] = self._store_params[-1][param]
        self._store_params.pop()
        self._unbury_indices(note, index)

    def _passes_final_checks(self) -> bool:
        for check in self._final_checks:
            if not check(): 
                # print("failed final check:", check.__name__)
                return False 
        return True 

    ######################################
    ### melodic insertion checks #########

    def _check_starting_pitch(self, note: Note) -> bool:
        if note.get_accidental() == ScaleOption.REST:
            return True 
        if note.get_scale_degree() != self._mr.get_final(): return False 
        return note.get_accidental() == ScaleOption.NATURAL
        
    def _check_last_pitch(self, note: Note) -> bool:
        if self._mr.get_final() != note.get_scale_degree() or note.get_accidental() != ScaleOption.NATURAL: return False
        if self._counterpoint_lst[-1].get_scale_degree_interval(note) == 2: 
            return self._mr.is_unison(self._mr.get_leading_tone_of_note(note), self._counterpoint_lst[-1])
        if self._counterpoint_lst[-1] != -2: return False 
        return self._mr.is_unison(self._counterpoint_lst[-1], self._mr.get_leading_tone_of_note(note))

    def _handles_adjacents(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        (sdg_interval, chro_interval) = self._mr.get_intervals(self._counterpoint_lst[-1], note)
        if sdg_interval not in LegalIntervalsFifthSpecies["adjacent_melodic_scalar"]: 
            return False 
        if chro_interval not in LegalIntervalsFifthSpecies["adjacent_melodic_chromatic"]: 
            return False 
        if (sdg_interval, chro_interval) in LegalIntervalsFifthSpecies["forbidden_combinations"]: 
            return False 
        return True 

    def _handles_interval_order(self, note: Note, index: tuple) -> bool:
        potential_interval = self._counterpoint_lst[-1].get_scale_degree_interval(note)
        if potential_interval >= 3:
            for i in range(len(self._counterpoint_lst) - 2, -1, -1):
                interval = self._counterpoint_lst[i].get_scale_degree_interval(self._counterpoint_lst[i + 1])
                if interval < 0: return True 
                if interval > 2: return False 
        if potential_interval == 2:
            segment_has_leap = False
            for i in range(len(self._counterpoint_lst) - 2, -1, -1):
                interval = self._counterpoint_lst[i].get_scale_degree_interval(self._counterpoint_lst[i + 1])
                if interval < 0: return True 
                if segment_has_leap: return False 
                segment_has_leap = interval > 2
        if potential_interval == -2:
            segment_has_leap = False
            for i in range(len(self._counterpoint_lst) - 2, -1, -1):
                interval = self._counterpoint_lst[i].get_scale_degree_interval(self._counterpoint_lst[i + 1])
                if interval > 0: return True 
                if segment_has_leap or interval == -8: return False 
                segment_has_leap = interval < -2
        if potential_interval <= -3:
            for i in range(len(self._counterpoint_lst) - 2, -1, -1):
                interval = self._counterpoint_lst[i].get_scale_degree_interval(self._counterpoint_lst[i + 1])
                if interval > 0: return True 
                if interval < -2: return False 
        return True 

    def _handles_nearby_augs_and_dims(self, note: Note, index: tuple) -> bool:
        if len(self._counterpoint_lst) < 2: return True
        if self._mr.is_cross_relation(note, self._counterpoint_lst[-2]) and self._counterpoint_lst[-1].get_duration() <= 2: return False 
        if self._counterpoint_lst[-2].get_duration() != 2 and self._counterpoint_lst[-1].get_duration() != 2: return True 
        (sdg_interval, chro_interval) = self._mr.get_intervals(self._counterpoint_lst[-2], note)
        return (abs(sdg_interval) != 2 or abs(chro_interval) != 3) and (abs(sdg_interval) != 3 or abs(chro_interval) != 2)

    def _handles_nearby_leading_tones(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat == 2 and (bar - 1, 2) in self._counterpoint_obj and self._counterpoint_obj[(bar - 1, 2)].get_duration() > 4:
            if self._mr.is_sharp(self._counterpoint_obj[(bar - 1, 2)]) and self._counterpoint_obj[(bar - 1, 2)].get_chromatic_interval(note) != 1:
                return False 
        if beat == 0 and bar != 0:
            prev_measure_notes = []
            for i, num in enumerate([0, 1, 1.5, 2, 3]):
                if (bar - 1, num) in self._counterpoint_obj and self._mr.is_sharp(self._counterpoint_obj[(bar - 1, num)]):
                    resolved = False
                    for j in range(i + 1, 5):
                        next_index = (bar - 1, [0, 1, 1.5, 2, 3][j])
                        if next_index in self._counterpoint_obj and self._counterpoint_obj[(bar - 1, num)].get_chromatic_interval(self._counterpoint_obj[next_index]) == 1:
                            resolved = True 
                    if not resolved and self._counterpoint_obj[(bar - 1, num)].get_chromatic_interval(note) != 1:
                        return False 
        return True 

    def _handles_ascending_minor_sixth(self, note: Note, index: tuple) -> bool:
        if len(self._counterpoint_lst) < 2: return True 
        if self._counterpoint_lst[-2].get_chromatic_interval(self._counterpoint_lst[-1]) == 8:
            return self._counterpoint_lst[-1].get_chromatic_interval(note) == -1
        return True

    def _handles_ascending_quarter_leaps(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if self._counterpoint_lst[-1].get_scale_degree_interval(note) > 2:
            if beat % 2 == 1: return False 
            if len(self._counterpoint_lst) >= 2 and self._counterpoint_lst[-1].get_duration() == 2:
                if self._counterpoint_lst[-2].get_scale_degree_interval(self._counterpoint_lst[-1]) > 0: return False
        return True 

    def _handles_descending_quarter_leaps(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if len(self._counterpoint_lst) < 2: return True 
        if self._counterpoint_lst[-2].get_scale_degree_interval(self._counterpoint_lst[-1]) < -2 and self._counterpoint_lst[-1].get_duration() == 2:
            if self._counterpoint_lst[-1].get_scale_degree_interval(note) == 2: return True 
            return self._counterpoint_lst[-2].get_scale_degree_interval(note) in [-2, 1, 2]
        return True 

    def _handles_repetition(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if self._mr.is_unison(self._counterpoint_lst[-1], note) and (beat != 2 or self._counterpoint_lst[-1].get_duration() != 2):
            return False 
        return True 

    def _handles_eigths(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if beat == 1.5 and abs(self._counterpoint_lst[-1].get_scale_degree_interval(note)) != 2: return False 
        if beat != 2: return True 
        if self._counterpoint_lst[-1].get_duration() != 1: return True 
        first_interval = self._counterpoint_lst[-3].get_scale_degree_interval(self._counterpoint_lst[-2])
        second_interval = self._counterpoint_lst[-2].get_scale_degree_interval(self._counterpoint_lst[-1])
        third_interval = self._counterpoint_lst[-1].get_scale_degree_interval(note)
        if abs(third_interval) != 2 or (second_interval == 2 and third_interval == -2) or (first_interval == 2 and second_interval == -2): return False 
        return True 

    def _handles_highest(self, note: Note, index: tuple) -> bool:
        if self._attempt_params["highest_has_been_placed"] and self._mr.is_unison(self._attempt_params["highest"], note):
            return False 
        return True 

    def _handles_resolution_of_anticipation(self, note: Note, index: tuple) -> bool:
        if len(self._counterpoint_lst) < 2 or not self._mr.is_unison(self._counterpoint_lst[-2], self._counterpoint_lst[-1]):
            return True 
        return self._counterpoint_lst[-1].get_scale_degree_interval(note) == -2

    def _handles_repeated_two_notes(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if len(self._counterpoint_lst) < 3: return True 
        if not self._mr.is_unison(self._counterpoint_lst[-3], self._counterpoint_lst[-1]) or not self._mr.is_unison(self._counterpoint_lst[-2], note):
            return True 
        if self._counterpoint_lst[-1].get_scale_degree_interval(note) != 2: return False 
        if self._counterpoint_lst[-2].get_duration() != 8 or beat != 0: return False 
        return True

    def _handles_quarter_between_two_leaps(self, note: Note, index: tuple) -> bool:
        if self._counterpoint_lst[-1].get_duration() != 2 or len(self._counterpoint_lst) < 2: return True 
        first_interval, second_interval = self._counterpoint_lst[-2].get_scale_degree_interval(self._counterpoint_lst[-1]), self._counterpoint_lst[-1].get_scale_degree_interval(note)
        if abs(first_interval) == 2 or abs(second_interval) == 2:
            return True 
        if first_interval > 0 and second_interval < 0: return False 
        if first_interval == -8 and second_interval == 8: return False 
        return True 

    def _handles_upper_neighbor(self, note: Note, index: tuple) -> bool:
        (bar, beat) = index
        if ( beat % 2 == 0 and self._counterpoint_lst[-1].get_duration() == 2 and  
            self._counterpoint_lst[-1].get_scale_degree_interval(note) == -2 and len(self._counterpoint_lst) >= 2 and 
            self._counterpoint_lst[-2].get_scale_degree_interval(self._counterpoint_lst[-1]) == 2 and 
            self._counterpoint_lst[-2].get_duration() != 2 ): return False 
        return True 

    def _handles_antipenultimate_bar(self, note: Note, index: tuple) -> bool:
        if index == (self._length - 3, 2):
            if note.get_accidental() != ScaleOption.NATURAL or note.get_scale_degree() != self._mr.get_final():
                return False 
        return True 
        

    ######################################
    ########## rhythms filters ###########

    def _get_durations_from_beat(self, beat: int) -> set:
        if beat == 1.5: return { 1 }
        if beat == 3: return { 2 }
        if beat == 1: return { 1, 2 }
        if beat == 2: return { 2, 4, 6, 8 }
        if beat == 0: return { 2, 4, 6, 8, 12 }

    def _handles_consecutive_quarters(self, note: Note, index: tuple, durs: set) -> set:
        (bar, beat) = index
        if self._counterpoint_lst[-1].get_duration() != 2: return durs 
        if self._counterpoint_lst[-1].get_scale_degree_interval(note) > 0 and beat == 2: durs.discard(4)
        if beat == 2 and self._counterpoint_lst[-2].get_duration() == 2 and self._counterpoint_lst[-3].get_duration() != 2:
            durs.discard(4)
        for i in range(len(self._counterpoint_lst) - 2, -1, -1):
            if self._counterpoint_lst[i].get_duration() != 2:
                return durs 
            if abs(self._counterpoint_lst[i].get_scale_degree_interval(self._counterpoint_lst[i + 1])) > 2:
                durs.discard(2)
                return durs 

    def _handles_penultimate_bar(self, note: Note, index: tuple, durs: set) -> set:
        (bar, beat) = index 
        if bar != self._length - 2: return durs 
        if beat == 2: 
            durs.discard(8)
            durs.discard(6)
            durs.discard(2)
        if beat == 0:
            durs.discard(12)
        return durs

    def _handles_first_eighth(self, note: Note, index: tuple, durs: set) -> set:
        (bar, beat) = index 
        if (beat == 1 and abs(self._counterpoint_lst[-1].get_scale_degree_interval(note)) != 2) or self._attempt_params["eighths_have_been_placed"]:
            durs.discard(1)
        if beat == 2 and self._counterpoint_lst[-1].get_duration() == 1 and self._counterpoint_lst[-3].get_duration() == 2:
            durs.discard(4)
            durs.discard(8)
            durs.discard(6)
        return durs 

    def _handles_sharp_durations(self, note: Note, index: tuple, durs: set) -> set:
        if self._mr.is_sharp(note): durs.discard(12)
        return durs 

    def _handles_whole_note_quota(self, note: Note, index: tuple, durs: set) -> set:
        (bar, beat) = index 
        if self._attempt_params["num_on_beat_whole_notes_placed"] == self._attempt_params["max_on_beat_whole_notes"]:
            if beat == 0: 
                durs.discard(8) 
                durs.discard(12)
        return durs

    def _handles_repeated_note(self, note: Note, index: tuple, durs: set) -> set:
        if self._mr.is_unison(self._counterpoint_lst[-1], note): 
            durs.discard(4)
            durs.discard(2)
        return durs

    def _handles_rhythm_after_descending_quarter_leap(self, note: Note, index: tuple, durs: set) -> set:
        (bar, beat) = index
        if self._counterpoint_lst[-1].get_duration() == 2 and self._counterpoint_lst[-1].get_scale_degree_interval(note) < -2:
            durs.discard(8)
            durs.discard(12)
            durs.discard(6)
        return durs

    def _handles_dotted_whole_after_quarters(self, note: Note, index: tuple, durs: set) -> set:
        if self._counterpoint_lst[-1].get_duration() == 2: durs.discard(12)
        return durs

    def _handles_repeated_dotted_halfs(self, note: Note, index: tuple, durs: set) -> set:
        (bar, beat) = index 
        if (bar - 1, beat) in self._counterpoint_obj and self._counterpoint_obj[(bar - 1, beat)].get_duration() == 6:
            durs.discard(6)
        return durs

    def _handles_antipenultimate_rhythm(self, note: Note, index: tuple, durs: set) -> set:
        if index == (self._length - 3, 2): 
            durs.discard(4)
            durs.discard(2)
        if index == (self._length - 3, 0):
            durs.discard(8)
            durs.discard(6)
        return durs 

    ##########################################
    ########### index checks #################

    def _highest_and_lowest_placed(self, index: tuple) -> bool:
        (bar, beat) = index 
        if bar >= self._attempt_params["highest_must_appear_by"] and not self._attempt_params["highest_has_been_placed"]:
            return False 
        if bar >= self._attempt_params["lowest_must_appear_by"] and not self._attempt_params["lowest_has_been_placed"]:
            return False 
        return True 

    ##########################################
    ########### insert functions #############

    def _bury_indices(self, note: Note, index: tuple) -> None:
        (bar, beat) = index
        self._stored_indices.append([])
        for i in range(1, note.get_duration()):
            new_beat, new_bar = beat + (i / 2), bar
            while new_beat >= 4:
                new_beat -= 4
                new_bar += 1
            if (new_bar, new_beat) in self._counterpoint_obj:
                self._stored_indices[-1].append((new_bar, new_beat))
                del self._counterpoint_obj[(new_bar, new_beat)]
                self._all_indices.remove((new_bar, new_beat))
                self._remaining_indices.remove((new_bar, new_beat))

    def _unbury_indices(self, note: Note, index: tuple) -> None:
        i = len(self._counterpoint_lst) + 1
        while len(self._stored_indices[-1]) > 0:
            next_index = self._stored_indices[-1].pop()
            self._all_indices.insert(i, next_index)
            self._remaining_indices.append(next_index)
            self._counterpoint_obj[next_index] = None
        self._stored_indices.pop()

    def _check_for_highest_and_lowest(self, note: Note, index: tuple) -> None:
        if self._mr.is_unison(note, self._attempt_params["highest"]):
            self._attempt_params["highest_has_been_placed"] = True 
        if self._mr.is_unison(note, self._attempt_params["lowest"]):
            self._attempt_params["lowest_has_been_placed"] = True 

    def _check_for_on_beat_whole_note(self, note: Note, index: tuple) -> None:
        (bar, beat) = index 
        if beat == 0 and note.get_duration() >= 8:
            self._attempt_params["num_on_beat_whole_notes_placed"] += 1

    def _check_if_new_run_is_added(self, note: Note, index: tuple) -> None:
        run_length = 0
        for i in range(len(self._counterpoint_lst) - 1, -1, -1):
            dur = self._counterpoint_lst[i].get_duration()
            if dur > 2: 
                break 
            run_length += dur / 2
        # if run_length > 7:
        #     print("run length:", run_length)
        if run_length == 4:
            self._attempt_params["num_runs_placed"] += 1
        if run_length == self._attempt_params["min_length_of_max_quarter_run"]:
            self._attempt_params["max_quarter_run_has_been_placed"] = True 

    def _check_if_eighths_are_added(self, note: Note, index: tuple) -> None:
        (bar, beat) = index 
        if beat == 1.5: self._attempt_params["eighths_have_been_placed"] = True

    ##########################################
    ########### final checks #################

    def _parameters_are_correct(self) -> bool:
        # print("num runs placed:", self._attempt_params["num_runs_placed"])
        # print("max run has been placed?", self._attempt_params["max_quarter_run_has_been_placed"])
        return self._attempt_params["num_runs_placed"] >= self._attempt_params["min_runs_of_length_4_or_more"] and self._attempt_params["max_quarter_run_has_been_placed"]

    def _has_only_one_octave(self) -> bool:
        num_octaves = 0
        for i in range(0 if self._counterpoint_lst[0].get_accidental() != ScaleOption.REST else 1, len(self._counterpoint_lst) - 1):
            if abs(self._counterpoint_lst[i].get_scale_degree_interval(self._counterpoint_lst[i + 1])) == 8:
                num_octaves += 1
                if num_octaves > 1: 
                    return False 
        return True 


    ##########################################
    ########### scoring ######################

    def _score_solution(self, solution: list[Note]) -> int:
        score = 0
        self._map_solution_onto_counterpoint_dict(solution)
        if (self._length - 2, 0) in self._counterpoint_obj: score += 500
        num_ties = 0
        num_tied_dotted_halfs = 0
        num_tied_wholes = 0
        ties = [False] * (self._length - 2)
        for i in range(1, self._length - 1):
            if (i, 0) not in self._counterpoint_obj: 
                ties[i - 1] = True
                num_ties += 1
                if (i - 1, 2) in self._counterpoint_obj:
                    if self._counterpoint_obj[(i - 1, 2)].get_duration() == 6:
                        num_tied_dotted_halfs += 1
                    else:
                        num_tied_wholes += 1
        ideal_ties = 3 if self._length < 12 else 4 
        score += abs(ideal_ties - num_ties) * 10 
        score += abs(num_tied_wholes - num_tied_dotted_halfs) * 7
        has_isolated_tie = False
        for i in range(1, len(ties) - 1):
            if ties[i - 1] == False and ties[i] == True and ties[i + 1] == False:
                has_isolated_tie = True 
        if has_isolated_tie: score += 12
        return score 

    def _map_solution_onto_counterpoint_dict(self, solution: list[Note]) -> None:
        self._counterpoint_obj = {}
        self._counterpoint_lst = []
        self._all_indices = []
        bar, beat = 0, 0
        self._all_indices = []
        for note in solution:
            self._counterpoint_obj[(bar, beat)] = note
            self._counterpoint_lst.append(note)
            self._all_indices.append((bar, beat))
            beat += note.get_duration() / 2 
            while beat >= 4:
                beat -= 4
                bar += 1