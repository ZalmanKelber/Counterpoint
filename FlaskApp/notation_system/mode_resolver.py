import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from notation_system.notational_entities import Mode, VocalRange, Accidental, Pitch, Note, Rest, Hexachord


#provides methods that return information about which pitches should be used in various
#scenarios based on the mode
class ModeResolver:

    _mode = None 

    def __init__(self, mode: Mode):
        self._mode = mode 


    #returns the Scale Degree of the mode "final" or "tonic"
    def get_mode_final(self) -> int:
        if self._mode == Mode.IONIAN: return 1
        if self._mode == Mode.DORIAN: return 2
        if self._mode == Mode.PHRYGIAN: return 3
        if self._mode == Mode.LYDIAN: return 4
        if self._mode == Mode.MIXOLYDIAN: return 5
        if self._mode == Mode.AEOLIAN: return 6

    #returns the Scale Degree of the mode's leading tone.  It is one note down in all modes except Phrygian
    def get_mode_leading_tone(self) -> int:
        if self._mode == Mode.IONIAN: return 7
        if self._mode == Mode.DORIAN: return 1
        if self._mode == Mode.PHRYGIAN: return 4
        if self._mode == Mode.LYDIAN: return 3
        if self._mode == Mode.MIXOLYDIAN: return 4
        if self._mode == Mode.AEOLIAN: return 5

    #determines whether a note is the mode's final
    def is_final(self, pitch: Pitch) -> bool:
        return pitch.get_accidental() == Accidental.NATURAL and pitch.get_scale_degree() == self.get_mode_final()

    #determines whether a note is the mode's leading tone
    def is_leading_tone(self, pitch: Pitch) -> bool:
        if pitch.get_scale_degree() != self.get_mode_leading_tone(): return False 
        if self._mode == Mode.IONIAN: return pitch.get_accidental() == Accidental.NATURAL
        if self._mode == Mode.DORIAN: return pitch.get_accidental() == Accidental.SHARP
        if self._mode == Mode.PHRYGIAN: return pitch.get_accidental() == Accidental.NATURAL
        if self._mode == Mode.LYDIAN: return pitch.get_accidental() == Accidental.NATURAL
        if self._mode == Mode.MIXOLYDIAN: return pitch.get_accidental() == Accidental.SHARP
        if self._mode == Mode.AEOLIAN: return pitch.get_accidental() == Accidental.SHARP

    #determines if a note is higher than the default pitch of its scale degree
    def is_sharp(self, pitch: Pitch) -> bool:
        if self._mode in [Mode.DORIAN, Mode.LYDIAN] and pitch.get_scale_degree() == 7:
            return pitch.get_accidental() == Accidental.NATURAL
        else: return pitch.get_accidental() == Accidental.SHARP

    #ranges are based on the followeing: 
    #Bass: G3 to D5, Tenor: D4 to A5, Alto: G4 to D6, Soprano: D5 to A6

    #returns lowest pitch of each voice range
    def get_lowest_of_range(self, vocal_range: VocalRange) -> Pitch:
        if vocal_range == VocalRange.BASS: return Pitch(5, 3)
        if vocal_range == VocalRange.TENOR: return Pitch(2, 4)
        if vocal_range == VocalRange.ALTO: return Pitch(5, 4)
        if vocal_range == VocalRange.SOPRANO: return Pitch(2, 5)

    #returns highest pitch of each voice range
    def get_highest_of_range(self, vocal_range: VocalRange) -> Pitch:
        if vocal_range == VocalRange.BASS: return Pitch(2, 5)
        if vocal_range == VocalRange.TENOR: return Pitch(6, 5)
        if vocal_range == VocalRange.ALTO: return Pitch(2, 6)
        if vocal_range == VocalRange.SOPRANO: return Pitch(6, 6)

    #returns default final to be used as starting and ending points for Cantus Firmus examples
    def get_default_mode_final(self, vocal_range: VocalRange) -> Pitch:
        if self._mode == Mode.IONIAN:
            if vocal_range == VocalRange.SOPRANO: return Pitch(1, 6)
            if vocal_range in [VocalRange.TENOR, VocalRange.ALTO]: return Pitch(1, 5)
            else: return Pitch(1, 4)
        if self._mode == Mode.DORIAN:
            if vocal_range == VocalRange.BASS: return Pitch(2, 4)
            else: return Pitch(2, 5)
        if self._mode == Mode.PHRYGIAN:
            if vocal_range in [VocalRange.ALTO, VocalRange.SOPRANO]: return Pitch(3, 5)
            else: return Pitch(3, 4)
        if self._mode == Mode.LYDIAN:
            if vocal_range in [VocalRange.ALTO, VocalRange.SOPRANO]: return Pitch(4, 5)
            else: return Pitch(4, 4)
        if self._mode == Mode.MIXOLYDIAN:
            if vocal_range in [VocalRange.ALTO, VocalRange.SOPRANO]: return Pitch(5, 5)
            else: return Pitch(5, 4)
        if self._mode == Mode.AEOLIAN:
            if vocal_range in [VocalRange.ALTO, VocalRange.SOPRANO]: return Pitch(6, 5)
            else: return Pitch(6, 4)
        

    #returns the two pitches (separated by a fifth) that an imitative theme at the beginning of a 
    #composition should outline, in the form of scale degrees
    #note that in all cases, the pitches are natural 

    #also, note once again that the "Hexachords" are not the three actual Hexachords of 
    #Medieval and Renaissance Muisc Theory but rather simplified proxies for representing 
    #Sharp and Flat directions of the Tonal Spectrum
    def get_outline_pitches(self, hexachord: Hexachord) -> list[int]:
        if self._mode == Mode.IONIAN: 
            if hexachord == Hexachord.MOLLE: return [1, 5]
            if hexachord == Hexachord.DURUM: return [2, 5]
        if self._mode == Mode.DORIAN: 
            if hexachord == Hexachord.MOLLE: return [2, 6]
            if hexachord == Hexachord.DURUM: return [3, 6]
        if self._mode == Mode.PHRYGIAN: 
            if hexachord == Hexachord.MOLLE: return [3, 6]
            if hexachord == Hexachord.DURUM: return [3, 7]
        if self._mode == Mode.LYDIAN: 
            if hexachord == Hexachord.MOLLE: return [1, 4]
            if hexachord == Hexachord.DURUM: return [1, 5]
        if self._mode == Mode.MIXOLYDIAN: 
            if hexachord == Hexachord.MOLLE: return [1, 5]
            if hexachord == Hexachord.DURUM: return [2, 5]
        if self._mode == Mode.AEOLIAN: 
            if hexachord == Hexachord.MOLLE: return [2, 6]
            if hexachord == Hexachord.DURUM: return [3, 6]

    #returns the set of available pitches that are a given interval from another given pitch
    #imputting A, -3 in all modes will return [F natural, F sharp]
    #note that these are tonal intervals and not chromatic intervals
    def get_pitches_from_interval(self, pitch: Pitch, interval: int) -> list[Pitch]:
        if interval == 0:
            raise Exception("0 is an invalid interval")
        sdg = pitch.get_scale_degree()
        octv = pitch.get_octave()
        adjustment_value = -1 if interval > 0 else 1
        new_sdg, new_octv = sdg + interval + adjustment_value, octv
        while new_sdg < 1:
            new_octv -= 1
            new_sdg += 7
        while new_sdg > 7:
                new_octv += 1
                new_sdg -= 7
        available_pitches = [Pitch(new_sdg, new_octv)]
        if new_sdg == 7 and self._mode in [Mode.DORIAN, Mode.LYDIAN]:
            available_pitches.insert(0, Pitch(new_sdg, new_octv, Accidental.FLAT))
        if (new_sdg == 2 and self._mode == Mode.AEOLIAN) or new_sdg in [1, 4, 5]:
            available_pitches.append(Pitch(new_sdg, new_octv, Accidental.SHARP))
        return available_pitches

    #returns the "default" pitch option for a Scale Degree.  Natural unless B in Dorian or Lydian in which case Flat 
    def get_default_pitch_from_interval(self, pitch: Pitch, interval: int) -> Pitch:
        return self.get_pitches_from_interval(pitch, interval)[0]


