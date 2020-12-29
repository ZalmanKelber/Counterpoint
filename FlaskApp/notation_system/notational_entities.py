from enum import Enum 

class Accidental (Enum):
    FLAT = 1
    NATURAL = 2
    SHARP = 3

class Mode (Enum):
    IONIAN = 1
    DORIAN = 2
    PHRYGIAN = 3
    LYDIAN = 4
    MIXOLYDIAN = 5
    AEOLIAN = 6

#ranges are based on the followeing: 
#Bass: G3 to D5, Tenor: D4 to A5, Alto: G4 to D6, Soprano: D5 to A6
class VocalRange (Enum):
    BASS = 1
    TENOR = 2
    ALTO = 3
    SOPRANO = 4

#these are not the actual Hexachords from Medieval and Renaissance Music Theory 
#but quick proxies to suggest a flat (Molle) or sharp (Durum) orientation
class Hexachord (Enum):
    MOLLE = 1
    DURUM = 2

class NotationalEntity:
    pass

class Pitch:

    #Scale Degrees 1 - 7 are the notes of a C Major scale
    #Octave is standard Octave Number from Scientific Pitch Notation
    _scale_degree = None
    _octave = None
    _accidental = None

    def __init__(self, scale_degree: int, octave: int, accidental: Accidental = Accidental.NATURAL):
        if scale_degree < 1 or scale_degree > 7:
            raise Exception("invalid scale degree")
        self._scale_degree = scale_degree
        self._octave = octave 
        self._accidental = accidental

    def __str__(self) -> str:
        name = ""
        if self._scale_degree == 1: name = "C "
        if self._scale_degree == 2: name = "D "
        if self._scale_degree == 3: name = "E "
        if self._scale_degree == 4: name = "F "
        if self._scale_degree == 5: name = "G "
        if self._scale_degree == 6: name = "A "
        if self._scale_degree == 7: name = "B "
        if self._accidental == Accidental.FLAT: name += "FLAT      "
        if self._accidental == Accidental.NATURAL: name += "NATURAL   "
        if self._accidental == Accidental.SHARP: name += "SHARP     "
        name += str(self._octave)
        return name.ljust(15)

    def get_scale_degree(self) -> int: return self._scale_degree

    def get_octave(self) -> int: return self._octave 

    def get_accidental(self) -> Accidental: return self._accidental

    #returns chromatic pitch value (C Naturals are multiples of twelve) used by standard MIDI applications
    def get_pitch_value(self) -> int:
        pitch_value = self._octave * 12

        if self._scale_degree == 1: pitch_value += 0
        elif self._scale_degree == 2: pitch_value += 2
        elif self._scale_degree == 3: pitch_value += 4
        elif self._scale_degree == 4: pitch_value += 5
        elif self._scale_degree == 5: pitch_value += 7
        elif self._scale_degree == 6: pitch_value += 9
        elif self._scale_degree == 7: pitch_value += 11

        if self._accidental == Accidental.FLAT: pitch_value -= 1
        elif self._accidental == Accidental.SHARP: pitch_value += 1

        return pitch_value

    #returns standard interval number.  Two notes separated by a Diminished Third, Minor Third, Major Third and 
    #Augmented Third will all return += 3.  Unison returns 1
    def get_tonal_interval(self, other_pitch: "Pitch") -> int:
        octv_difference = (other_pitch.get_octave() - self._octave) * 7
        sdg_difference = other_pitch.get_scale_degree() - self._scale_degree
        diff = octv_difference + sdg_difference
        return diff + 1 if diff >= 0 else diff - 1

    #returns number of Chromatic Notes (Half Steps) by which two notes are removed.  
    #Unison returns 0 and Octaves return 12 or negative 12
    def get_chromatic_interval(self, other_pitch: "Pitch") -> int:
        return other_pitch.get_pitch_value() - self.get_pitch_value() 

    #returns both of the above as a tuple
    def get_intervals(self, other_pitch: "Pitch") -> tuple[int, int]:
        return (self.get_tonal_interval(other_pitch), self.get_chromatic_interval(other_pitch))

    #determines if two pitches are unison (the same pitch and spelled the same -- enharmonic equivalents return False)
    def is_unison(self, other_pitch: "Pitch") -> bool:
        return ( other_pitch.get_octave() == self._octave and 
            other_pitch.get_scale_degree() == self._scale_degree and 
            other_pitch.get_accidental() == self._accidental )

    #determines if two pitches (not necessarily in the same octave) are cross relations (e.g. B Natural and B Flat)
    def is_cross_relation(self, other_pitch: "Pitch") -> bool:
        return other_pitch.get_scale_degree() == self._scale_degree and other_pitch.get_accidental() != self._accidental

class RhythmicValue:

    #durations are in number of Eighth Notes (NOT number of Beats)
    _duration = None

    def __init__(self, duration: int):
        if duration < 0: 
            raise Exception("cannot have negative value")
        self._duration = duration 

    def get_duration(self) -> int: return self._duration 

    #only durations that are valid in 16th Century Counterpoint have names
    def __str__(self) -> str:
        name = ""
        if self._duration == 1: name = "EIGHTH NOTE"
        elif self._duration == 2: name = "QUARTER NOTE"
        elif self._duration == 4: name = "HALF NOTE"
        elif self._duration == 6: name = "DOTTED HALF NOTE"
        elif self._duration == 8: name = "WHOLE NOTE"
        elif self._duration == 12: name = "DOTTED WHOLE NOTE"
        elif self._duration == 16: name = "BREVE"
        else: name = "DURATION: " + str(self._duration)
        return name.ljust(18)

class Rest(RhythmicValue):

    def __init__(self, duration: int):
        super().__init__(duration)

    def __str__(self):
        return "REST".ljust(15) + super().__str__()

class Note(RhythmicValue, Pitch):

    def __init__(self, duration: int, scale_degree: int, octave: int, accidental: Accidental = Accidental.NATURAL):
        RhythmicValue.__init__(self, duration)
        Pitch.__init__(self, scale_degree, octave, accidental)

    def __str__(self) -> str:
        return Pitch.__str__(self) + RhythmicValue.__str__(self)

