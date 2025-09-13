# Create tiling using Smith-Myers-Kaplan-Goodman-Strauss hat tiles.
#
# Copyright 2025, Ray Griner
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the “Software”),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

'''Create tiling using Smith-Myers-Kaplan-Goodman-Strauss hat tiles.

The configuration of the tiles matches that in the GIF animation on the
page https://cs.uwaterloo.ca/~csk/hat/. See LICENSE.txt for complete
attribution details.

The tile generation isn't particularly elegant here. We put the first tile
down and use a configuration file to specify how the other ~200 tiles are
placed, by matching an edge of the new tile to an edge on a tile that was
already placed. So extending this program to even larger grids is probably
not advisable.

The program can probably be extended without too much effort to use the
other tiles in the family described by the authors in their paper (i.e.,
the tiles in the continuum from 'chevron' to 'comet').
'''

import math

from hat_family import AllTiles

#-----------------------------------------------------------------------------
# Main Entry Point
#-----------------------------------------------------------------------------

all_tiles = AllTiles(tile_param1=1, tile_param2=math.sqrt(3),
              chiralities={'lb': 'L', 'w': 'L', 'db': 'R', 'g': 'L'},
              colors={'lb': '#66ccff', 'w': '#ffffff', 'db': '#006699',
                      'g': '#A0A0A0'},
              first_tile_angle=2*math.pi*(14/360))

all_tiles.add_all_tiles(input_file_name = 'hat_config.txt')

all_tiles.footnote = all_tiles.footnote.replace('BASED_ON_TILING',
    'the hat tiling')

all_tiles.set_crop_values(
              left_x=all_tiles.get_pt(tile_id='40', edge='LS')[0],
              bottom_y=all_tiles.get_pt(tile_id='244', edge='LP')[1],
              right_x=all_tiles.get_pt(tile_id='160', edge='RN')[0],
              top_y=all_tiles.get_pt(tile_id='220', edge='LN')[1]
                         )

all_tiles.write_points_to_file('hat_tiling.txt')
