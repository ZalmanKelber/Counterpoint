# Counterpoint Project (in progress)

## Project goals

**Main goal:** create computer-generated small musical compositions in the style of 16th century counterpoint -- a style of foundational importance to Western Music Theory and central to hundreds of years of Music Pedagogy.  Using the analysis of this style by **Knud Jeppesen** as a guide, generate compositions in the style of standard species counterpoint pedagogical exercises and then work up to compositions in the style of the 16th century composer **Giovanni Pierluigi da Palestrina**, whose liturgical vocal works are often used to represent this style.

**Specifically:**

* Develop a system of representing musical pitch and rhythm from scratch, using python3.  This notational system will need to easily represent pitches both chromatically and as diatonic scale degrees.<sup>[[1]](#notes)</sup>

* Use a combination of random number generators and backtracking algorithms to create short (5-20 seconds) compositions in accordance with the highly complex set of rules<sup>[[2]](#notes)</sup> outlined by Jeppesen for different compositional exercises.  In order:

  * Cantus Firmus

  * Two-Part Counterpoint: First Species through Fifth Species, Free Counterpoint, Imitation

  * Three-Part Counterpoint: First Species through Fifth Species, Imitation

  * Four-Part Counterpoint: First Species through Fifth Species, Imitation

* Transform the project into a backend API endpoint (probably with Flask) and add a frontend UI (probably in React) that plays back the resulting compositions

**Possible longer term goals:**

* Supplement Jeppesen's rules with basic Machine Learning and input exisiting compositions by Palestrina

* Incorporate and build on existing research into computerized generation of Palestrina-style counterpoint, such as [this study](https://quod.lib.umich.edu/i/icmc/bbp2372.2001.003/1/--analysis-and-synthesis-of-palestrina-style-counterpoint?page=root;size=100;view=text) that uses probabilistic Markov chains

## Project progress and updates

* Dec 1 2020: added basic system for [representing musical notation](https://github.com/ZalmanKelber/Counterpoint/blob/main/notation_system.py).  This system is designed to be easy to use in the highly specific style of 16th-century counterpoint: each `Note` object contains four properties: an octave (these are standard [integer octave identification numbers](https://musictheorytutoring.weebly.com/octave-identification.html)), a scale degree integer (1-7 = C-B), a duration in eighth notes (legal values in this style are 1, 2, 4, 6, 8, 12, 16) and a `Scale_option` ENUM (options are `FLAT`, `NATURAL` and `SHARP`).  The `get_chromatic()` method returns the chromatic value of the note (0-11 = C-B).  It is thus easy to compare two notes and determine if the interval they form is, for example, a "sixth" (scale degrees differ by five) or if they are specifically a "minor sith" (chromatic values differ by 8)

* Dec 2 2020: added program that [generates a cantus firmus](https://github.com/ZalmanKelber/Counterpoint/blob/main/cantus_firmus.py).  Jeppesen doesn't give rules for Cantus Firmus examples, so the following were used, based on standard Cantus Firmus guidelines and the author's observations about Jeppesen's examples:

  * Based on Jeppesen's examples: length is between 8 and 12 notes

  * Common rule: start and end on the mode 'final'

  * Common rule: highest note can only appear once and cannot be in the exact middle

  * Based on Jeppsen's examples: range from highest to lowest note can be 5th, 6th, 7th or octave

  * Based on Jeppesen's examples: The interval between the final and the highest note, and the interval between the final and the lowest note, must be melodically consonant<sup>[[3]](#notes)</sup>

  * If the total range is an octave, the final must be a fourth or fifth above the lowest note

  * Based on Jeppesen's examples: In the Dorian mode, B-natural cannot be the highest note

  * Jeppesen: in ascending motion, larger (scale degree-based) intervals cannot follow smaller ones, and the reverse is true in descending motion

  * Common rule: melody cannot outline melodically dissonant intervals 

  * Based on Jeppesen's examples: in any sequence of consecutive leaps, no two notes can be a melodically dissonant interval apart

  * Simplification: B-flats can only be used in Dorian and Lydian and B-flat and B-natural cannot appear in the same Cantus Firmus.  No sharps are used

  * Based on Jeppesen's examples: the penultimate note is extremely likely to be a step above the final but can also be the step below the final or the most common cadence note of a mode (also below the final in this case)

  * Common rule: avoid sequences and repetition.  Interpreted by the author to exclude the following: any immediate repeat of two notes, any subsequent repeats of three notes, and any subsequent repeats of three (scale degree-based) intervals

  * Based on Jeppesen's examples: the ratio of intervals that are steps should be close to around .7

  The programming sequence that generates a Cantus Firmus runs as follows:

  * If none are provided, a length, mode and octave are randomly chosen.  The first and final notes of the Cantus Firmus are set to the 'final' -- the chief note of the mode in the specified octave

  * The possible highest notes are generated and one is randomly chosen.  Based on this and the final, the possible lowest notes are generated and one is randomly chosen

  * If a randomly generated number is greater than .9, the penultimate note is set as the step above the final.  Otherwise, if possible, it's set as either the most common cadence note or step below 

  * If we have not already placed the highest note in the Cantus Firmus by way of the preceding step, we select all legal unfilled indices with which we could place it and shuffle them.  The highest note is placed in the first index in which its placement doesn't cause any irresolvable problems with its immediate neighbors<sup>[[4]](#notes)</sup>

  * Likewise, if the lowest note is not already present, we place it in a random legal index

  * The set of all legal notes is generated.  This includes all scale degrees from the lowest note to the note below the highest note

  * We now backtrack through the unfilled indices.  For each possible note in the set of all legal notes, we first evaluate if placing it in the specified index causes any immediate conflicts with its neighbors.  We then test if the current chain (the consecutive thus-far filled indices from the beginning of the Cantus Firmus) is legal according to several criteria 

  * When we reach the end, we run additional checks on the Cantus Firmus to see if it's legal before adding it to our set of solutions (and then backtracking again)

  * When the backtracking algorithm is complete, we see if the list of solutions is empty.  If it is, we start the entire process over again 

  * We then sort the solutions according to how closely the ratio of steps to toal intervals in a solution matches the average of Jeppesen's examples, and return a `CantusFirmus` object with the first solution 

  * Average runtime for this process is about 35 milliseconds 

* Dec 3 2020: added program that creates [two part first species exercises](https://github.com/ZalmanKelber/Counterpoint/blob/main/two_part_first_species.py) but there are still violations (detailed below).  This exercise introduces considerably greater complexity, although there are some loosening on the rules of melody from the plain Cantus Firmus examples.  Namely:

  * Jeppesen: incorrect ordering of larger and smaller intervals is forgiven when "segments" are limited to three or fewer intervals and intervals are no greater than thirds 

  However, melodies are now considerably more complex:

  * Sharps are now permitted (on C, F and G as well as D# in Aeolian)

  * If the Counterpoint is in the upper voice, it may start and/or end a fifth above the mode's "final"

  We now consider the requirements of harmony:

  * Consonant intervals only, exluding augmented and diminished enharmonic equivalents (TO DO: fix remaining violations)

  * Unisons not permitted except on first and last note 

  And the rules of counterpoint:

  * Parallel fifths and octaves as well as hidden fifths and octaves may not occur 

  * The Counterpoint and Cantus Firmus cannot be separated by the same (scale degree-based) harmonic interval for more than four consecutive notes

  * If both voices leap in the same direction, neither leap can be greater than a fourth (TO DO: fix remaining violations)

  TO DO: find a method of scoring the resulting exercises and use those scores to sort them and find the optimal solutions

### Notes:

1. The *equal temperment* will be used for all pitch representation, and historical tuning will be considered well beyond the scope of this project

2. At this time, the appropriateness of using analytical rules (specifically, those of Jeppesen) to emulate a historical style (that is, 16th century sacred vocal music in the style of Palestrina), won't be examined in detail 

3. Throughout, a distinction will be employed between *melodically consonant* and *melodically dissonant* intervals (the latter includes only sevenths and augmented and diminished intervals) and *melodically permissible* and *melodically inpermissible* intervals (among sixths, only ascending minor sixths are permitted)

4. There are scenarios, nevertheless, where the placement of the highest and/or lowest notes does cause irresolvable conflicts.  These are taken into consideration later