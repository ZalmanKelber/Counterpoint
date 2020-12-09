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
    FLAT = "FLT"
    NATURAL = "NAT"
    SHARP = "SHP"
    REST = "REST"

class RangeOption (Enum):
    SOPRANO = "SOPRANO"
    ALTO = "ALTO"
    TENOR = "TENOR"
    BASS = "BASS"

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
        if self._accidental == ScaleOption.REST: return 0
        return self.get_chromatic() + self._octave * 12

    def get_scale_degree_interval(self, other_note) -> int:
        octv_difference = (other_note.get_octave() - self._octave) * 7
        sdg_difference = other_note.get_scale_degree() - self._scale_degree
        diff = octv_difference + sdg_difference
        return diff + 1 if diff >= 0 else diff - 1

    def get_chromatic_interval(self, other_note) -> int:
        return other_note.get_chromatic_with_octave() - self.get_chromatic_with_octave()


    def __str__(self) -> str:
        if self.get_accidental() == ScaleOption.REST: return "REST"
        pitch_value = PITCH_NAMES[self.get_scale_degree()] + " " + self.get_accidental().value
        rhythmic_value = RHYTHM_NAMES[self.get_duration()]
        if self.get_duration() == 1:
            return "%s %d," % (pitch_value, self.get_octave())
        return "%s %d, %s NOTE" % (pitch_value, self.get_octave(), rhythmic_value)

class ModeResolver: 
    def __init__(self, mode: ModeOption, range_option: RangeOption = RangeOption.ALTO):
        self._mode = mode 
        self._range = range_option

    def get_lowest(self) -> Note:
        sdg, octv = None, None 
        if self._range == RangeOption.BASS: sdg, octv = 5, 3
        if self._range == RangeOption.TENOR: sdg, octv = 2, 4
        if self._range == RangeOption.ALTO: sdg, octv = 5, 4
        if self._range == RangeOption.SOPRANO: sdg, octv = 2, 5
        return Note(sdg, octv, 8, ScaleOption.NATURAL)

    def get_highest(self) -> Note:
        sdg, octv = None, None 
        if self._range == RangeOption.BASS: sdg, octv = 2, 4
        if self._range == RangeOption.TENOR: sdg, octv = 6, 4
        if self._range == RangeOption.ALTO: sdg, octv = 2, 5
        if self._range == RangeOption.SOPRANO: sdg, octv = 6, 5
        return Note(sdg, octv, 8, ScaleOption.NATURAL)

    def is_leading_tone(self, note: Note) -> bool:
        return note.get_accidental() == ScaleOption.SHARP or (note.get_scale_degree() == 7 and self._mode in [ModeOption.DORIAN, ModeOption.LYDIAN])

    def is_sharp(self, note: Note) -> bool:
        return self.is_leading_tone(note)
    
    def resolve_b(self) -> ScaleOption: #determines if default is b or b-flat, depending on mode
        if self._mode == ModeOption.DORIAN or self._mode == ModeOption.LYDIAN:
            return ScaleOption.FLAT #default is b-flat for dorian and lydian
        else:
            return ScaleOption.NATURAL #default is b natural for ionian, phrygian, mixolydian and aeolian 

    def is_legal(self, note: Note) -> bool:
        if note.get_scale_degree() in [1, 2, 3, 4, 5, 6] and note.get_accidental() == ScaleOption.FLAT:
            return False #we don't allow c-flat, d-flat, e-flat (for now), f-flat, g-flat or a-flat
        if note.get_scale_degree() in [2, 3, 6, 7] and note.get_accidental() == ScaleOption.SHARP:
            return False #we don't allow d-sharp (for now), e-sharp, a-sharp or b-sharp
        return True 

    def is_unison(self, note1: Note, note2: Note) -> bool:
        return note1.get_scale_degree_interval(note2) == 1 and note1.get_chromatic_interval(note2) == 0 

    def is_cross_relation(self, note1: Note, note2: Note) -> bool:
        return abs(note1.get_scale_degree_interval(note2)) in [1, 8, 15] and abs(note1.get_chromatic_interval(note2)) not in [0, 12, 24]

    def get_intervals(self, note1: Note, note2: Note) -> tuple:
        return (note1.get_scale_degree_interval(note2), note1.get_chromatic_interval(note2))

    def get_default_scale_option(self, scale_degree: int) -> ScaleOption:
        if scale_degree <= 6:
            return ScaleOption.NATURAL
        else:
            return self.resolve_b()

    def make_default_scale_option(self, note: Note) -> None:
        sdg = note.get_scale_degree()
        note.set_accidental(self.get_default_scale_option(sdg))

    def get_final(self) -> int:
        if self._mode == ModeOption.IONIAN: return 1
        if self._mode == ModeOption.DORIAN: return 2
        if self._mode == ModeOption.PHRYGIAN: return 3
        if self._mode == ModeOption.LYDIAN: return 4
        if self._mode == ModeOption.MIXOLYDIAN: return 5
        if self._mode == ModeOption.AEOLIAN: return 6

    def get_leading_tone_of_note(self, note: Note) -> Note:
        lt = self.get_default_note_from_interval(note, -2)
        if lt.get_scale_degree() in [1, 4, 5] or (lt.get_scale_degree() == 2 and self._mode == ModeOption.AEOLIAN):
            lt.set_accidental(ScaleOption.SHARP)
        if lt.get_scale_degree() == 7:
            lt.set_accidental(ScaleOption.NATURAL)
        return lt

    def get_default_note_from_interval(self, note: Note, interval: int) -> Note:
        candidates = self.get_notes_from_interval(note, interval)
        if len(candidates) == 0: return None 
        note = candidates[0]
        self.make_default_scale_option(note)
        return note
    
    #returns valid notes, if any, at the specified interval.  "3" returns a third above.  "-5" returns a fifth below
    def get_notes_from_interval(self, note: Note, interval: int) -> list[Note]: 
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


        

