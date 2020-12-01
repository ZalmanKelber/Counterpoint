from enum import Enum 

#valid rhythmic values (stored as number of eighth notes) include eighth notes, quarter notes,
#dotted quarter notes, half notes, dotted half notes, whole notes, dotted whole notes and breves
VALID_DURATIONS = {1, 2, 4, 6, 8, 12, 16} 
SCALE_DEGREES_TO_CHROMATIC = { 1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11 }

#use an enum to keep track of which mode we're in 
#(we won't consider the distinction between standard and plagal modes)
class Mode_option (Enum):
    IONIAN = "IONIAN"
    DORIAN = "DORIAN"
    PHRYGIAN = "PHRYGIAN"
    LYDIAN = "LYDIAN"
    MIXOLYDIAN = "MIXOLYDIAN"
    AEOLIAN = "AEOLIAN"

class Scale_option (Enum):
    FLAT = "FLAT"
    NATURAL = "NATURAL"
    SHARP = "SHARP"

#contains scale degree, accidental, octave (standard octave identification)
#and duration (in eighth notes) and 
class Note:

    def __init__(self, scale_degree: int, octave: int, duration: int, accidental: Scale_option = Scale_option.NATURAL): 
        if duration not in VALID_DURATIONS:
            raise Exception("invalid rhythmic value")
        if scale_degree not in range(1, 8):
            raise Exception("invalid scale degree")
        self._scale_degree = scale_degree
        self._octave = octave
        self._accidental = accidental
        self._duration = duration 

    def get_scale_degree(self) -> int: return self._scale_degree
    
    def get_accidental(self) -> Scale_option: return self._accidental 

    def get_octave(self) -> int: return self._octave

    def get_duration(self) -> int: return self._duration 

    def set_scale_degree(self, scale_degree: int) -> None: 
        if scale_degree not in range(1, 8):
            raise Exception("invalid scale degree")
        self._scale_degree = scale_degree
    
    def set_accidental(self, accidental: Scale_option) -> None: self._accidental = accidental

    def set_octave(self, octave: int) -> None: self._octave = octave

    def set_duration(self, duration: int) -> None: 
        if duration not in VALID_DURATIONS:
            raise Exception("invalid rhythmic value")
        self._duration = duration

    def get_chromatic(self) -> int: #returns chromatic pitch representation of note in range (0, 12)
        chro_val = SCALE_DEGREES_TO_CHROMATIC[self._scale_degree]
        if self._accidental == Scale_option.SHARP:
            chro_val += 1
        elif self._accidental == Scale_option.FLAT:
            chro_val -= 1
        return chro_val
    
    def get_chromatic_with_octave(self) -> int: #useful for comparing pitch values of two notes
        return self.get_chromatic() + self._octave * 12

class ModeResolver: 
    def __init__(self, mode: Mode_option):
        self.mode = mode 
    
    def resolve_b(self) -> Scale_option: #determines if default is b or b-flat, depending on mode
        if self.mode == Mode_option.DORIAN or self.mode == Mode_option.LYDIAN:
            return Scale_option.FLAT #default is b-flat for dorian and lydian
        else:
            return Scale_option.NATURAL #default is b natural for ionian, phrygian, mixolydian and aeolian 

    def is_legal(self, note: Note) -> bool:
        if note.get_scale_degree() in [1, 2, 3, 4, 5, 6] and note.get_accidental() == Scale_option.FLAT:
            return False #we don't allow c-flat, d-flat, e-flat (for now), f-flat, g-flat or a-flat
        if note.get_scale_degree() in [2, 3, 6, 7] and note.get_accidental() == Scale_option.SHARP:
            return False #we don't allow d-sharp (for now), e-sharp, a-sharp or b-sharp
        return True 

    def get_scale_option(self, scale_degree: int) -> Scale_option:
        if scale_degree <= 6:
            return Scale_option.NATURAL
        else:
            return self.resolve_b()

        

