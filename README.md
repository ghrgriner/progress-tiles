# Summary

This is a generalization of a 'progress bar'.
It displays tiles in a pattern chosen by the user and then
listens on a FIFO for messages that include the denominator and
then numerators of what percent of work is done and modifies
the tiles shown based on the percentage of work done, e.g., by
changing color or transparency of some percentage of the tiles
from a 'start' to a 'done' state.

The order the tiles are toggled are random, except the border
tiles are toggled first. The `BORDER_FIRST` parameter in `show_progress.py`
can be changed to disable this.

The program is written using GTK4 with Python bindings, so GTK
and the Python libraries will need to be installed to be run.
It was tested on Linux. Since FIFOs are implemented differently
on Windows, it probably needs modification to run on that platform.

The program was originally written for use with a custom add-on
for the (desktop version of) Anki flashcard software that
sends the messages as flashcards are reviewed. The code for this
add-on is [available for download on Ankiweb](https://ankiweb.net/shared/info/1300160579).

Additional technical details are in the docstring headers of the
programs.

Currently, the program blocks until a writer connects to the FIFO.

# Configuration

The coordinates of the (polygonal) tiles to display are read from
a text file named 'tiling.txt'. The file should have the variables:
- px_0, py_0, ..., px_n, py_n - Coordinates of the tile. Tiles can
  have different number of vertices, with pairs left blank for tiles
  with vertices fewer than the maximum. The value (0,0) will be
  displayed in the upper left of the display window.
- image_width, image_height - Image width and height. This is unitless,
  but the scale should match that defined by the `px_` and `py_`
  coordinates. If the aspect window in the display window doesn't match
  the aspect ratio defined by these values, then the excess height or
  width will not be displayed.
- start_fill_color, start_stroke_color, done_fill_color, done_stroke_color
  (optional) - define the the default fill and stroke (tile border)
  colors in rgb or rgba hex notation (e.g., '#ff00bc' or 'de303080')
  for both the 'start' and 'done' states.
- footnote (optional) - if the column exists, then the value from the
  first row (if it exists) will be used as a footnote to the image.

The following environment variables are used by the program:

- SHOW_PROGRESS_FIFO: The path to the FIFO the program will
  listen on.
- SHOW_PROGRESS_START_FILL_COLOR: Default start fill color, if not
  provided in the input text file. If not set, default is '#FF0000' (red).
- SHOW_PROGRESS_START_STROKE_COLOR: Default start stroke color, if not
  provided in the input text file. If not set, defaults to the start
  fill color.
- SHOW_PROGRESS_DONE_FILL_COLOR: Default done fill color, if not
  provided in the input text file. If not set, default is '#00A933' (green).
- SHOW_PROGRESS_DONE_STROKE_COLOR: Default done stroke color, if not
  provided in the input text file. If not set, defaults to the 'done'
  fill color.

# Example

Three classes of example input text files are provided.

The different examples can be run by setting the `TILE_FILE_NAME` parameter
in `show_progress.py` to the appropriate `*_tiling.txt` file.

1. An example using the Smith-Myers-Kaplan-Goodman-Strauss 'hat' tiles [1],
   where tiles change from opaque to transparent. See `LICENSE.txt` for
   license and attribution information for this example. This example
   defines about 250 tiles. The exact number displayed depends on the cropping,
   but the minimal cropping appears to yield 166 tiles entirely shown with
   additional partial tiles on the image border. We have also provided
   code (`hatlike.py`) and coordinates (`turtle_tiling.txt`,
   `tile_10_1_tiling.txt`, etc.) for eight other tiles in the hat-like family
   described in [1].
2. A larger example using the 'hat' tiles. Again, see `LICENSE.txt` for
   the license and attribution information. This example defines 656 tiles.
   The exact number displayed depends on the cropping, but the maximum is
   probably about 550 tiles entirely shown. To run this example, set
   `TILE_FILE_NAME=hat2_tiling.txt` in `show_progress.py` and rerun.
3. An example where tiles in a honeycomb pattern change from shades of red
   to shades of green. This example consist of 90 tiles. To run this example,
   set `TILE_FILE_NAME=honeycomb_tiling.txt` in `show_progress.py` and rerun.

Screenshots of the examples can be found [on the wiki](https://github.com/ghrgriner/progress-tiles/wiki/Examples), although for point (1), we currently only 
have screenshots for the 'hat' tile.

# Running the Program

Run the program with `python3 show_progress.py`. It's not necessary to run
the other python files, as these make the `*_tiling.txt` input files, which
are already provided.

# References

[1] Smith D, Myers JS, Kaplan CS, Goodman-Strauss C. An aperiodic monotile. Combinatorial Theory, 4(1):1-91.
