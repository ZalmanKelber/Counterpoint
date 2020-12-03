import sys
sys.path.insert(0, "/Users/alexkelber/Development/MIDIUtil/src")

from midiutil import MIDIFile

from notation_system import Note 

class MidiWriter:
    def write_midi_from_counterpoint(self, lines: list[list[Note]], filename: str) -> None:
        # degrees  = [60, 62, 64, 65, 67, 69, 71, 72]  # MIDI note number
        # track    = 0
        # channel  = 0
        # time     = 0    # In beats
        # duration = 1    # In beats
        # tempo    = 60   # In BPM
        # volume   = 100  # 0-127, as per the MIDI standard

        # MyMIDI = MIDIFile(1)  # One track, defaults to format 1 (tempo track is created
        #                     # automatically)
        # MyMIDI.addTempo(track, time, tempo)

        # for i, pitch in enumerate(degrees):
        #     MyMIDI.addNote(track, channel, pitch, time + i, duration, volume)
        tempo = 672
        volume = 100
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
                CounterpointMIDI.addNote(track, channel, pitch, time_index, duration, volume)
                time_index += duration
        with open(filename, "wb") as output_file:
            CounterpointMIDI.writeFile(output_file)




# with open("major-scale.mid", "wb") as output_file:
#     MyMIDI.writeFile(output_file)