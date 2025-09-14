# Create tiling using Smith-Myers-Kaplan-Goodman-Strauss hat-family tiles.
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

'''Create tiling using Smith-Myers-Kaplan-Goodman-Strauss hat-family tiles.

The configuration of the tiles matches that in the GIF animation on the
page https://cs.uwaterloo.ca/~csk/hat/. See ../LICENSE.txt for complete
attribution details.

The tile generation isn't particularly elegant here. We put the first tile
down and use a configuration file to specify how the other ~200 tiles are
placed, by matching an edge of the new tile to an edge on a tile that was
already placed. So extending this program to even larger grids is probably
not advisable.
'''

import math

from hat_family import AllTiles, get_angle, Segment

from collections import namedtuple
HatLike = namedtuple('HatLike',
                     ['param1','param2','based_on','output_file','ref'],
                     defaults=['N'])

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
examples_to_make = [
    HatLike(param1=1, param2=0, output_file='comet_tiling.txt',
            based_on="a 'comet' tiling"),
    HatLike(param1=10, param2=1, output_file='tile_10_1_tiling.txt',
            based_on='a Tile(10, 1) tiling'),
    HatLike(param1=4, param2=1, output_file='tile_4_1_tiling.txt',
            based_on="a Tile(4, 1) tiling"),
    HatLike(param1=math.sqrt(3), param2=1, output_file='turtle_tiling.txt',
            based_on="a 'turtle' tiling"),
    HatLike(param1=1, param2=1, output_file='tile_1_1_tiling.txt',
            based_on="a Tile(1, 1) tiling"),
    HatLike(param1=1, param2=math.sqrt(3), output_file='hat_tiling.txt',
            based_on="the hat tiling", ref='Y'),
    HatLike(param1=1, param2=4, output_file='tile_1_4_tiling.txt',
            based_on="a Tile(1, 4) tiling"),
    HatLike(param1=1, param2=10, output_file='tile_1_10_tiling.txt',
            based_on="a Tile(1, 10) tiling"),
    HatLike(param1=0, param2=1, output_file='chevron_tiling.txt',
            based_on="a chevron tiling"),
           ]

#-----------------------------------------------------------------------------
# Main Entry Point
#-----------------------------------------------------------------------------
chiralities = {'lb': 'L', 'w': 'L', 'db': 'R', 'g': 'L'}
colors = {'lb': '#66ccff', 'w': '#ffffff', 'db': '#006699', 'g': '#A0A0A0'}
all_tiles = AllTiles(tile_param1=1, tile_param2=math.sqrt(3),
              chiralities=chiralities, colors=colors,
              first_tile_angle=2*math.pi*(14/360))
all_tiles.add_all_tiles(input_file_name = 'hat_config.txt')

pt1o = all_tiles.get_pt(tile_id='28', edge='LP')
pt2o = all_tiles.get_pt(tile_id='189', edge='LP')

for example in examples_to_make:
    all_tiles2 = AllTiles(tile_param1=example.param1,
                          tile_param2=example.param2,
              chiralities=chiralities, colors=colors,
              first_tile_angle=2*math.pi*(14/360))
    all_tiles2.add_all_tiles(input_file_name = 'hat_config.txt')

    all_tiles2.footnote = all_tiles2.footnote.replace('BASED_ON_TILING',
            example.based_on)

    pt1n = all_tiles2.get_pt(tile_id='28', edge='LP')
    pt2n = all_tiles2.get_pt(tile_id='189', edge='LP')

    if example.ref != 'Y':
        all_tiles2.change_coordinates(Segment(start=pt1o, stop=pt2o),
                      Segment(start=pt1n, stop=pt2n))

    all_tiles2.set_crop_values(
              left_x=all_tiles.get_pt(tile_id='40', edge='LS')[0],
              bottom_y=all_tiles.get_pt(tile_id='244', edge='LP')[1],
              right_x=all_tiles.get_pt(tile_id='160', edge='RN')[0],
              top_y=all_tiles.get_pt(tile_id='220', edge='LN')[1]
                          )

    all_tiles2.write_points_to_file('tilings/hat/' + example.output_file)
