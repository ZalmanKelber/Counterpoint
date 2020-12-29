import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from notation_system.notational_entities import RhythmicValue, Pitch, Rest, Accidental, VocalRange, Note

class TemplateWriter:
    def write_template_from_counterpoint(self, counterpoint: list[list[RhythmicValue]], lines: list[VocalRange], filename: str) -> None:
        with open(filename, "w") as output_file:
            output_file.write("\\new StaffGroup << ")
            for line in range(len(lines) - 1, -1, -1):
                clef = get_clef(lines[line])
                output_file.write('\n \\new Staff { \\clef "' + clef + '" ')
                beat = 0
                for entity in counterpoint[line]:
                    output_file.write(get_string_representation_of_entity(entity, beat))
                    beat += entity.get_duration() / 2
                    beat %= 4
                output_file.write(' \\bar "|." } ')
            output_file.write("\n >>")

    
def get_string_representation_of_entity(entity: RhythmicValue, beat: float) -> str:
    #determine if the Note or Rest goes over to the next Bar
    split_note = entity.get_duration() / 2 > 4 - beat
    string_representation = " "
    if isinstance(entity, Rest):
        string_representation += "r"
    else:
        string_representation += {
            1: "c", 2: "d", 3: "e", 4: "f", 5: "g", 6: "a", 7: "b"
        }[entity.get_scale_degree()]


        string_representation += {
            Accidental.NATURAL: "", Accidental.SHARP: "is", Accidental.FLAT: "es"
        }[entity.get_accidental()]

        octave = entity.get_octave()
        if octave > 4:
            string_representation += "'" * (octave - 4)
        if octave < 4:
            string_representation += "," * (4 - octave)

    string_representation += {
        8: "1", 6: "2.", 4: "2", 2: "4", 1: "8"
    }[entity.get_duration()] if not split_note else "1" if beat == 0 else "2"

    if split_note:
        second_note = Note(entity.get_duration() - ((4 - beat) * 2), entity.get_scale_degree(), entity.get_octave(), entity.get_accidental())
        string_representation += "~" + get_string_representation_of_entity(second_note, 0)
    
    return string_representation

def get_clef(vocal_range: VocalRange) -> str:
    if vocal_range == VocalRange.BASS:
        return "bass"
    if vocal_range == VocalRange.TENOR:
        return "tenorG"
    return "treble"