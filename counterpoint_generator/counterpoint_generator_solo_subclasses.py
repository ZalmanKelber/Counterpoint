from filter_functions.melodic_insertion_checks import last_interval_is_descending_step

from counterpoint_generator_species_subclasses import FirstSpeciesCounterpointGenerator
from counterpoint_generator_subclasses import SoloMelody

class CantusFirmusGenerator (FirstSpeciesCounterpointGenerator, SoloMelody):

    def __init__(self, length: int, lines: list[VocalRange], mode: Mode):
        super().__init__(length, lines, mode)
        SoloMelody().__init__(self, length, lines, mode)

        #Add the end by descending step optional function
        self._melodic_insertion_checks.append(last_interval_is_descending_step)
    
    #override:
    #override the generate counterpoint function to provide the option of ending by descending step
    def generate_counterpoint(self, must_end_by_descending_step: bool = False) -> None:
        #this property is referenced by the last_interval_is_descending_step insertion check to determine whether 
        #or not to enforce the rule
        self._must_end_by_descending_step = must_end_by_descending_step
        super().generate_counterpoint()
