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

### Notes:

1. The *equal temperment* will be used for all pitch representation, and historical tuning will be considered well beyond the scope of this project

2. At this time, the appropriateness of using analytical rules (specifically, those of Jeppesen) to emulate a historical style (that is, 16th century sacred vocal music in the style of Palestrina), won't be examined in detail