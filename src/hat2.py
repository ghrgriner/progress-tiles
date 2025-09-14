# Create larger tiling using Smith-Myers-Kaplan-Goodman-Strauss hat tiles.
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

'''Create larger tiling using Smith-Myers-Kaplan-Goodman-Strauss hat tiles.

The configuration of the tiles matches that in image 'patch647.png' on the
page https://cs.uwaterloo.ca/~csk/hat/. See ../LICENSE.txt and the footnote
on the first (non-header) row of the input file for complete attribution
details.
'''

import math

from hat_family import AllTiles

#-----------------------------------------------------------------------------
# Main Entry Point
#-----------------------------------------------------------------------------

all_tiles = AllTiles(tile_param1=1, tile_param2=math.sqrt(3),
              chiralities={'r': 'R', 'w': 'R', 'db': 'L', 'g': 'R'},
              colors={'r': '#66ccff', 'w': '#ffffff', 'db': '#006699',
                      'g': '#A0A0A0'})

all_tiles.add_all_tiles(input_file_name = 'hat2_config.txt')

all_tiles.set_crop_values(
              left_x=all_tiles.get_pt(tile_id='254', edge='RT')[0],
              bottom_y=all_tiles.get_pt(tile_id='128', edge='LN')[1],
              right_x=all_tiles.get_pt(tile_id='457', edge='LN')[0],
              top_y=all_tiles.get_pt(tile_id='153', edge='LN')[1]
                         )

all_tiles.write_points_to_file('hat2_tiling.txt')

