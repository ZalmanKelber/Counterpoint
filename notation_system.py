from enum import Enum 

#valid rhythmic values (stored as number of eighth notes) include eighth notes, quarter notes,
#dotted quarter notes, half notes, dotted half notes, whole notes, dotted whole notes and breves
VALID_DURATIONS = { 1, 2, 4, 6, 8, 12, 16 } 
SCALE_DEGREES_TO_CHROMATIC = { 1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11 }

#use scale degree to get letter name of note and duration to get note rhythmic value
PITCH_NAMES = { 1: "C", 2: "D", 3: "E", 4: "F", 5: "G", 6: "A", 7: "B" }
RHYTHM_NAMES = { 1: "EIGHTH", 2: "QUARTER", 4: "HALF", 6: "DOTTED HALF", 8: "WHOLE", 12: "DOTTED WHOLE", 16: "BREVE" }

#use an enum to keep track of which mode we're in 
#(we won't consider the distinction between standard and plagal modes)
class ModeOption (Enum):
    IONIAN = { "name": "IONIAN", "starting": 1, "most_common": 5, "next_most_common": 6, "others": [2]}
    DORIAN = { "name": "DORIAN", "starting": 2, "most_common": 5, "next_most_common": 3, "others": [4, 7]}
    PHRYGIAN = { "name": "PHRYGIAN", "starting": 3, "most_common": 4, "next_most_common": 3, "others": [6, 7]}
    LYDIAN = { "name": "LYDIAN", "starting": 4, "most_common": 5, "next_most_common": 6, "others": [2]}
    MIXOLYDIAN = { "name": "MIXOLYDIAN", "starting": 5, "most_common": 5, "next_most_common": 4, "others": [2]}
    AEOLIAN = { "name": "AEOLIAN", "starting": 6, "most_common": 4, "next_most_common": 3, "others": [6, 7]}

class ScaleOption (Enum):
    FLAT = "FLAT"
    NATURAL = "NATURAL"
    SHARP = "SHARP"

#contains scale degree, accidental, octave (standard octave identification)
#and duration (in eighth notes) and 
class Note:

    def __init__(self, scale_degree: int, octave: int, duration: int, accidental: ScaleOption = ScaleOption.NATURAL): 
        if duration not in VALID_DURATIONS:
            raise Exception("invalid rhythmic value")
        if scale_degree not in range(1, 8):
            raise Exception("invalid scale degree")
        self._scale_degree = scale_degree
        self._octave = octave
        self._accidental = accidental
        self._duration = duration 

    def get_scale_degree(self) -> int: return self._scale_degree
    
    def get_accidental(self) -> ScaleOption: return self._accidental 

    def get_octave(self) -> int: return self._octave

    def get_duration(self) -> int: return self._duration 

    def set_scale_degree(self, scale_degree: int) -> None: 
        if scale_degree not in range(1, 8):
            raise Exception("invalid scale degree")
        self._scale_degree = scale_degree
    
    def set_accidental(self, accidental: ScaleOption) -> None: self._accidental = accidental

    def set_octave(self, octave: int) -> None: self._octave = octave

    def set_duration(self, duration: int) -> None: 
        if duration not in VALID_DURATIONS:
            raise Exception("invalid rhythmic value")
        self._duration = duration

    def get_chromatic(self) -> int: #returns chromatic pitch representation of note in range (0, 12)
        chro_val = SCALE_DEGREES_TO_CHROMATIC[self._scale_degree]
        if self._accidental == ScaleOption.SHARP:
            chro_val += 1
        elif self._accidental == ScaleOption.FLAT:
            chro_val -= 1
        return chro_val
    
    def get_chromatic_with_octave(self) -> int: #useful for comparing pitch values of two notes
        return self.get_chromatic() + self._octave * 12

    def get_scale_degree_interval(self, other_note) -> int:
        octv_difference = (other_note.get_octave() - self._octave) * 7
        sdg_difference = other_note.get_scale_degree() - self._scale_degree
        diff = octv_difference + sdg_difference
        return diff + 1 if diff >= 0 else diff - 1

    def get_chromatic_interval(self, other_note) -> int:
        return other_note.get_chromatic_with_octave() - self.get_chromatic_with_octave()


    def __str__(self) -> str:
        pitch_value = PITCH_NAMES[self.get_scale_degree()] + " " + self.get_accidental().value
        rhythmic_value = RHYTHM_NAMES[self.get_duration()]
        return "Note: pitch value = %s, octave = %d, duration = %s" % (pitch_value, self.get_octave(), rhythmic_value)

class ModeResolver: 
    def __init__(self, mode: ModeOption):
        self.mode = mode 
    
    def resolve_b(self) -> ScaleOption: #determines if default is b or b-flat, depending on mode
        if self.mode == ModeOption.DORIAN or self.mode == ModeOption.LYDIAN:
            return ScaleOption.FLAT #default is b-flat for dorian and lydian
        else:
            return ScaleOption.NATURAL #default is b natural for ionian, phrygian, mixolydian and aeolian 

    def is_legal(self, note: Note) -> bool:
        if note.get_scale_degree() in [1, 2, 3, 4, 5, 6] and note.get_accidental() == ScaleOption.FLAT:
            return False #we don't allow c-flat, d-flat, e-flat (for now), f-flat, g-flat or a-flat
        if note.get_scale_degree() in [2, 3, 6, 7] and note.get_accidental() == ScaleOption.SHARP:
            return False #we don't allow d-sharp (for now), e-sharp, a-sharp or b-sharp
        return True 

    def get_default_scale_option(self, scale_degree: int) -> ScaleOption:
        if scale_degree <= 6:
            return ScaleOption.NATURAL
        else:
            return self.resolve_b()


        

