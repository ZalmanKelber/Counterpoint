import sys
sys.path.insert(0, "/Users/alexkelber/Development/MIDIUtil/src")

from midiutil import MIDIFile

from notation_system import Note, ScaleOption

class MidiWriter:
    def write_midi_from_counterpoint(self, lines: list[list[Note]], filename: str) -> None:
        if lines is None: return
        tempo = 672
        channel = 0
        track = 0
        start_time = 0
        CounterpointMIDI = MIDIFile(1)
        CounterpointMIDI.addTempo(track, start_time, tempo)
        # for line in lines:
        for line in lines:
            time_index = start_time
            for note in line:
                duration = note.get_duration()
                pitch = note.get_chromatic_with_octave()
                volume = 0 if note.get_accidental() == ScaleOption.REST else 100
                CounterpointMIDI.addNote(track, channel, pitch, time_index, duration, volume)
                time_index += duration
        with open(filename, "wb") as output_file:
            CounterpointMIDI.writeFile(output_file)
           