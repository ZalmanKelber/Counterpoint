import sys
sys.path.insert(0, "/Users/alexkelber/Documents/Python/Jeppesen/notation_system")


from random import shuffle

from notational_entities import Pitch, RhythmicValue, Rest, Note, Mode, Accidental, VocalRange
from mode_resolver import ModeResolver

#an instance of a CounterpointGenerator creates a set of solutions through the generate_counterpoint() 
#method, scores and sorts the solutions through the score_solutions() method and returns the optimal solution
#or all solutions through the get_optimal() and get_all_solutions() methods

class CounterpointGenerator:

    #stores each line of counterpoint as a stack of notes that can be added and removed
    _counterpoint_stacks = []

    #stores each line of counterpoint in object form with tuples of form (bar, beat) as keys 
    #in order to look up notes by their rhythmic placement
    _counterpoint_objects = []

    #number of lines of counterpoint.  Default is one 
    _height = 1

    #a list of the lines of counterpoint, from bottom to top, in the form of the VocalRange of each line
    _lines = []

    #the mode in which the counterpoint is being written (represented by the Mode Enum)
    _mode = None

    #the ModeResolver object used to determine various information about the pitches based on the mode 
    _mode_resolver = None

    #number of measures of counterpoint (NB: final note values are breves, which have the length of two measures,
    # but are simplified here as constituting one single final measure)
    _length = None 

    #contains the available (bar, beat) locations for each line of counterpoint, including those that have already been 
    #filled with notes and those that remain.  When notes are added, the indices that the note is held over for are removed,
    #as no notes can be placed on them.  A whole note at the beginning of a bar will therefore remove all subsequent indices of that bar 
    _all_indices = []

    #the remaining indices of a line -- the places where notes may be added but have not been added yet.  Stored as a stack
    _remaining_indices = []

    #requirements for each line, that are generated arbitrarily during each attempt
    _attempt_parameters = []

    #the following items store a snapshot of the indices and attempt parameters prior to a note being inserted onto the stack.
    #when a note is inserted onto the stack, the conditions prior to its insertion are placed on these stacks as well so that they 
    #can be restored when a note is removed from the stack
    _store_all_indices_stacks = []
    _store_remaining_indices_stacks = []
    _store_deleted_indices_stacks = []
    _store_attempt_parameters_stacks = []

    #keeps track of the number of attempts an instance of a CounterpointGenerator has made
    _number_of_attempts = None

    #keeps track of the number of times the backtrack method has been called.  This and the above 
    #will form the basis for the exit conditions by which the backtrack algorithm is ended 
    _number_of_backtracks = 0

    #the list of functions that pitches will be passed through to deterine if they are eligible to be placed on
    #the stack at a given location in a line of counterpoint 
    _melodic_insertion_checks = []

    #each eligible pitch will then send a list of available rhythmic durations through these filters
    #to determine which pitch/rhythm combinations may be legally placed on the counterpoint stack
    _rhythmic_insertion_filters = []

    #every time a note or rest is added onto the counterpoint stack, these checks determine if adding the 
    #note changes any of the attempt parameters (for example, "highest_has_been_placed")
    _change_parameters_checks = []

    #index checks are run when a certain index (of the form (bar, beat)) is reached on the stack, in order
    #to determine whether or not certain conditions (specified in the attempt parameters) have been met
    _index_checks = []

    #final checks are run when the backtracking algorithm reaches the end of the remaining indices to determine
    #if a solution is legal, and thus whether it should be added to the list of solutions
    _final_checks = []

    #a list of solutions collected by the algorithm.  Each one is in the form of a list of lines of counterpoint,
    #each of which is a list of successive RhythmicValue objects (that is, Notes and Rests)
    _solutions = []

    #a list of scoring functions that add to the score of a solution -- used when selecting the optimal
    #solution from the ones added
    _score_functions = []

    #default list of valid intervals.  This will be changed or overriden in some but not all subclasses
    _legal_intervals = {
        "tonal_adjacent_melodic": { -8, -5, -4, -3, -2, 1, 2, 3, 4, 5, 6, 8 },
        "chromatic_adjacent_melodic": { -12, -7, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7, 8, 12 },
        "tonal_outline_melodic": { -10, -8, -6, -5, -4, -3, -2, 1, 2, 3, 4, 5, 6, 8, 10 },
        "chromatic_outline_melodic": { -16, -15, -12, -9, -8, -7, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7, 8, 9, 12, 15, 16 },
        #forbidden combinations of tonal intervals (absolute value, mod 7) and chromatic intervals (absolute value, mod 12)
        "forbidden_combinations": { (1, 1), (2, 3), (3, 2), (4, 4), (4, 6), (5, 6), (5, 8), (6, 10) }
    }

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        self._length = length 
        self._height = len(lines)
        self._lines = lines[:]
        self._mode = mode 
        self._mode_resolver = ModeResolver(mode)

        for line in range(self._height):
            self._counterpoint_stacks.append([])
            self._counterpoint_objects.append({})
            self._all_indices.append(set())
            self._remaining_indices.append([])
            self._attempt_parameters.append({ 
                "lowest": None, 
                "highest": None,
                "lowest_must_appear_by": None,
                "highest_must_appear_by": None,
                "highest_has_been_placed": None,
                "available_pitches": []
                })
            self._store_all_indices_stacks.append([])
            self._store_remaining_indices_stacks.append([])
            self._store_deleted_indices_stacks.append([])
            self._store_attempt_parameters_stacks.append([])

        #the following are the small number of default functions added to the checks
        self._index_checks.append(self._ensure_lowest_and_highest_have_been_placed)

        self._melodic_insertion_checks.append(self._valid_melodic_interval)
        self._melodic_insertion_checks.append(self._prevent_highest_duplicates)

        self._change_parameters_checks.append(self._check_for_lowest_and_highest)

    ###################### public functions ############################


    #the generate_counterpoint method runs a series of attempt loops, until certain specifications are met.
    #each attempt consists of an initialization, during which attempt parameters are arbitrarily generated
    #followed by the backtracking algorithm being run until the backtracking exit conditions are met
    def generate_counterpoint(self) -> None:
        self._number_of_attempts = 0
        while not self._exit_attempt_loop():
            self._number_of_attempts += 1
            self._initialize()
            self._backtrack()
        return 

    #sorts the solutions by the scording system (note that lower scores are better)
    def score_solutions(self) -> None:
        self._solutions.sort(key=lambda sol: self._score_solution(sol))

    #retrieves the first solution.  If the solutions have been sorted, this will be the optimal solution 
    #according to the scoring system
    def get_one_solution(self) -> list[list[RhythmicValue]]:
        return self._solutions[0] if len(self._solutions) > 0 else None 

    #retrieves all solutions
    def get_all_solutions(self) -> list[list[list[RhythmicValue]]]:
        return self._solutions

    #the function that determines when to stop running the attempts loop.  Default is given below, but will be 
    #overridden in all subclasses
    def _exit_attempt_loop(self) -> bool:
        if len(self._solutions) > 0 or self._number_of_attempts > 0: 
            return True 
        return False 

    def _score_solution(self, sol: list[list[RhythmicValue]]) -> int:
        self._map_solution_onto_stack
        score = 0
        for check in self._score_functions:
            score += check()
        return score 

    #takes a solution and maps it onto the counterpoint stack so that it can be more easily
    #examined by the scoring functions (which otherwise would not be able to look up notes and rests
    # by bar and beat)
    def _map_solution_onto_stack(self, sol: list[list[RhythmicValue]]) -> None:
        for line in range(self._height):
            self._counterpoint_objects[line] = {}
            self._counterpoint_stacks[line] = []
            self._all_indices[line] = set()
            self._remaining_indices[line] = []
            bar, beat = 0, 0
            for entity in sol[line]:
                self._counterpoint_stacks[line].append(entity)
                self._counterpoint_objects[line][(bar, beat)] = entity
                self._all_indices[line].add((bar, beat))
                beat += entity.get_duration() / 2
                while beat >= 4:
                    beat -= 4
                    bar += 1

    ############# initialize and helper functions ##########


    def _initialize(self) -> None:
        #reset the number of times the backtracking function has been called to zero
        self._number_of_backtracks = 0 

        #for each line, set up all of the indices and remaining indices 
        for line in range(self._height):
            for bar in range(self._length - 1):
                for beat in [0, 1, 1.5, 2, 3]:
                    self._all_indices[line].add((bar, beat))
                    self._remaining_indices[line].append((bar, beat))
                    self._counterpoint_objects[line][(bar, beat)] = None
            self._all_indices[line].add((self._length - 1, 0))
            self._remaining_indices[line].append((self._length - 1, 0))
            self._remaining_indices[line].reverse()
            self._counterpoint_objects[line][(bar, beat)] = None 

        #for each line, determine the highest and lowest notes, determine the measures by which they
        #must appear and collect the valid pitches that can be used 
        self._delineate_vocal_ranges()

    def _delineate_vocal_range(self) -> None:
        for line in range(self._height):
            self._attempt_parameters[line]["lowest_has_been_placed"] = False
            self._attempt_parameters[line]["highest_has_been_placed"] = False
            self._assign_highest_and_lowest()
            #now that the lowest and highest notes have been assigned, we can get all of the 
            #available pitches for each line.  Note that we're unconcerned with the order here
            self._attempt_parameters[line]["available_pitches"] = [
                self._attempt_parameters[line]["lowest"], 
                self._attempt_parameters[line]["highest"]
                ]
            for interval in range(2, self._attempt_parameters[line]["lowest"].get_tonal_interval(self._attempt_parameters[line]["highest"])):
                self._attempt_parameters[line]["available_pitches"] += self._mode_resolver.get_pitches_from_interval(self._attempt_parameters[line]["lowest"], interval)

    #note that this will be overriden in every subclass
    #this default method simply returns the lowest and highest notes of the available VocalRange object
    #and specifies that they must appear by the last measure
    def _assign_highest_and_lowest(self) -> None:
        for line in range(self._height):
            vocal_range = self._lines[line]
            self._attempt_parameters[line]["lowest"] = self._mode_resolver.get_lowest_of_range(vocal_range)
            self._attempt_parameters[line]["highest"] = self._mode_resolver.get_highest_of_range(vocal_range)
            self._attempt_parameters[line]["lowest_must_appear_by"] = self._length - 1
            self._attempt_parameters[line]["highest_must_appear_by"] = self._length - 1


    ############ backtrack and helper functions ###############

    #recursive function that adds successive notes onto the counterpoint stack until solutions are reached
    def _backtrack(self) -> None:
        self._number_of_backtracks += 1

        #first determine whether the loop should be exited
        if self._exit_backtrack_loop(): return 

        #determine which line we're in.  Lines are written one at a time from bottom to top, but in some 
        #subclasses, certain lines will be generated and added beforehand, so we can't be sure that the top line
        #will always be the last to be written 
        line = 0
        while line < self._height and len(self._remaining_indices[line]) == 0:
            line += 1
        
        #see if we've reached the end of the stack.
        #if so, see if the current stack passes the final checks, and if it does, add it to the solutions
        if line == self._height:
            if self._passes_final_checks():
                self._solutions.append([self._counterpoint_stacks[line][:] for line in range(self._height)])
            return 

        #otherwise, get the current index
        (bar, beat) = self._remaining_indices[line].pop()

        #make sure that the index checks are all true before preceding further
        if not self._passes_index_checks(line, bar, beat):
            return

        #get the valid pitches from available pitches by passing them through the insertion checks
        valid_pitches = filter(lambda pitch: self._passes_insertion_checks(pitch, line, bar, beat), self._attempt_parameters[line]["available_pitches"])
        valid_notes_and_rests = []
        for pitch in valid_pitches:
            #for each valid, pitch, get the valid rhythmic values and create a note for each valid combination
            for dur in self._get_valid_durations(pitch, line, bar, beat):
                valid_notes_and_rests.append(Note(dur, pitch.get_scale_degree(), pitch.get_octave(), pitch.get_accidental()))
        #add valid rests as well
        for dur in self._get_valid_rest_durations(line, bar, beat):
            valid_notes_and_rests.append(Rest(dur))
        #use the random module to shuffle the results
        shuffle(valid_notes_and_rests)

        for entity in valid_notes_and_rests:
            self._add_entity_to_stack(entity, line, bar, beat)
            #now that the entity is added to the stack, we can call the recursive backtracking function again
            self._backtrack()
            #now that the backtracking function has completed its course up to this point, remove the entity from the stack
            self._remove_entity_from_stack(line, bar, beat)

        self._remaining_indices.append((bar, beat))

    #the default is given below, but this should be overriden in every subclass
    def _exit_backtrack_loop(self) -> bool:
        if self._number_of_backtracks > 10000 or len(self._solutions) > 0:
            return True 
        return False 

    #runs a list of functions that examine the current stack to determine if it's valid
    def _passes_final_checks(self) -> bool:
        for check in self._final_checks:
            if not check(): return False 
        return True 

    #runs each pitch through a list of insertion checks to determine whether the pitch may be legally 
    #added to the stack at the specified location
    def _passes_insertion_checks(self, pitch: Pitch, line: int, bar: int, beat: float) -> bool:
        for check in self._melodic_insertion_checks:
            if not check(pitch, line, bar, beat): return False 
        return True 

    #runs each pitch through a list of checks that determine whether a given rhythmic value in combination with that pitch
    #can be legally placed on the stack at the specified location
    def _get_valid_durations(self, pitch: Pitch, line: int, bar: int, beat: float) -> set[int]:
        durations = get_available_durations(line, bar, beat)
        for check in self._rhythmic_insertion_filters:
            durations = check(pitch, line, bar, beat, durations)
        return durations

    #default method, which will be applicable to some subclasses
    #(lines may begin with a half note beat)
    def _get_valid_rest_durations(self, line: int, bar: int, beat: float) -> set[int]:
        if (bar, beat) == (0, 0): return { 4 }
        return set()

    #default available durations may be overridden by some subclasses
    def _get_available_durations(self, line: int, bar: int, beat: float) -> set[int]:
        if bar == self._length - 1: return { 16 }
        if beat == 1.5: return { 1 }
        if beat == 1: return { 1, 2 }
        if beat == 3: return { 2 }
        if beat == 2: return { 2, 4, 6, 8 }
        if beat == 0:
            if bar == 0: return { 2, 4, 6, 8, 12, 16 }
        return { 2, 4, 5, 8, 12 }

    #adds the note or rest to the stack, removes the indices that it nullifies, adds the current snapshot
    #of the attempt parameters to the stack of stored conditions and checks to see if any conditions have changed
    def _add_entity_to_stack(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> None:

        #add the note or rest to the stack
        self._counterpoint_stacks[line].append(entity)
        self._counterpoint_objects[line][(bar, beat)] = entity 

        #calculate the indices to remove (the beats on which notes can no longer be placed in order for successsive notes not to overlap)
        indices_to_remove = []
        new_bar, new_beat = bar, beat
        for half_beat in entity.get_duration() - 1: #we don't go to the end of the note or rest's rhythmic value, because
            new_beat += .5                               #the index immediately after it should remain 
            if new_beat >= 4:
                new_beat -= 4
                new_bar += 1
            if (new_bar, new_beat) in self._all_indices[line]:
                indices_to_remove.append((new_bar, new_beat))

        #store copies of the current indices and the current attempt parameters in the appropriate stacks
        self._store_deleted_indices_stacks.append(indices_to_remove)
        self._store_all_indices_stacks[line].append(self._all_indices[line][:])
        self._store_remaining_indices_stacks[line].append(self._remaining_indices[line][:])
        self._store_attempt_parameters_stacks[line].append(self._attempt_parameters[line].copy())
        
        #for each of the indices to remove, remove them from the _all_indices, _remaining_indices and _counterpoint_objects objects
        for index in indices_to_remove:
            del self._counterpoint_objects[line][index]
            self._all_indices[line].remove(index)
            self._remaining_indices[line].pop()

        #change the attempt paramters as appropriate 
        for check in self._change_parameters_checks:
            check(entity, line, bar, beat)

    def _remove_entity_from_stack(self, line: int, bar: int, beat: float) -> None:

        #remove the actual note or rest
        self._counterpoint_objects[line][(bar, beat)] = None 
        self._counterpoint_stacks[line].pop()

        #restore previous conditions
        self._attempt_parameters[line] = self._store_attempt_parameters_stacks[line].pop()
        self._all_indices[line] = self._store_all_indices_stacks[line].pop()
        self._remaining_indices[line] = self._store_remaining_indices_stacks[line].pop()

        #add each deleted index back to the counterpoint object 
        for index in self._store_deleted_indices_stacks[line].pop():
            self._counterpoint_objects[line][index] = None 


    ############################ default insertion (and other) checks ##################

    ################### index checks ####################

    def _ensure_lowest_and_highest_have_been_placed(self, line: int, bar: int, beat: float) -> bool:
        if not self._attempt_parameters[line]["lowest_has_been_placed"] and bar >= self._attempt_parameters[line]["lowest_must_appear_by"]:
            return False 
        if not self._attempt_parameters[line]["highest_has_been_placed"] and bar >= self._attempt_parameters[line]["highest_must_appear_by"]:
            return False 

    ################## melodic insertion filters ####################

    #ensures that all adjacent notes move by melodically legal intervals
    def _valid_melodic_interval(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> bool:
        if isinstance(entity, Pitch) and len(self._counterpoint_stacks[line]) > 0 and isinstance(self._counterpoint_stacks[line][-1], Pitch):
            (t_interval, c_interval) = self._counterpoint_stacks[line][-1].get_intervals(entity)
            if t_interval not in self._legal_intervals["tonal_adjacent_melodic"]: return False 
            if c_interval not in self._legal_intervals["chromatic_outline_melodic"]: return False
            if (abs(t_interval) % 7, abs(c_interval) % 12) in self._legal_intervals["forbidden_combinations"]: return False
        return True 

    #ensures that the highest note appears only once 
    def _prevent_highest_duplicates(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> bool:
        if ( isinstance(entity, Pitch) and 
            self._attempt_parameters[line]["highest_has_been_placed"] and 
            entity.is_unison(self._attempt_parameters[line]["highest"]) ):
            return False 
        return True 

    ################ change parameter checks #######################

    #determines whether inserted note is the highest or lowest
    def _check_for_lowest_and_highest(self, entity: RhythmicValue, line: int, bar: int, beat: float) -> None:
        if not isinstance(entity, Pitch): return 
        if entity.is_unison(self._attempt_parameters[line]["lowest"]):
            self._attempt_parameters[line]["lowest_has_been_placed"] = True 
        if entity.is_unison(self._attempt_parameters[line]["highest"]):
            self._attempt_parameters[line]["highest_has_been_placed"] = True 
