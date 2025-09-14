# Create tiling using Smith-Myers-Kaplan-Goodman-Strauss Tile(1,1) tiles.
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

'''Create spectre Smith-Myers-Kaplan-Goodman-Strauss tilings.

This generates a file with the vertices for the spectre tilings. The same
vertices can, for example, be used to draw Tile(1,1) tiles of a single
chirality.

The configuration of the tiles matches that in 
https://cs.uwaterloo.ca/~csk/spectre/examples/patch.png. See ../LICENSE.txt
for complete license and attribution details.

The tile generation isn't particularly elegant here. We put the first tile
down and use a configuration file to specify how the other ~300 tiles are
placed, by matching an edge of the new tile to an edge on a tile that was
already placed. So extending this program to even larger grids is probably
not advisable.
'''

import math
import csv

from hat_family import AllTiles, HatFamilyTile


#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------
# The edge names we use in the config file differ from the edge names used
# by HatFamilyTile. This dictionary maps the former to the latter.
TILE11_EDGE_RENAMER = {
  'LN': 'LP',  # left neck
  'LH': 'LH',  # left head
  'RH': 'LS',  # right head
  'RN': 'LN',  # right neck
  'RS': 'RN',  # right shoulder
  'BK': 'RS',  # back
  'RT': 'RH',  # right torso
  'RW': 'RP',  # right waist
  'RD': 'RT',  # right down
  'LD': 'RW',  # left down
  'LW': 'DW',  # left waist
  'LT': 'LW',  # left torso
  'LS': 'LT',  # left shoulder
  '': '',
}

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class AllTile11Tiles(AllTiles):
    '''Class for monochiral Tile(1,1) tiles

    This inherits from AllTiles. The only modification is `add_all_tiles` is
    the edge names are remapped when the input file is read (from the names
    used in the input file to the names expected by `HatFamilyTile`.
    '''
    def add_all_tiles(self, input_file_name):
        with open(input_file_name, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows_read = 0
            for row in reader:
                if rows_read == 0 and 'footnote' in row and row['footnote']:
                    self.footnote = row['footnote']
                self.add_hat(HatFamilyTile(all_tiles=self,
                    match_id=row['match_id'],
                    match_edge=TILE11_EDGE_RENAMER[row['match_edge']],
                    start_edge=TILE11_EDGE_RENAMER[row['start_edge']],
                    tile_id=row['tile_id'], color=row['color']))
                rows_read += 1

#-----------------------------------------------------------------------------
# Main Entry Point
#-----------------------------------------------------------------------------
chiralities = {'og': 'L', 'w': 'L'}
colors = {'og': '#8080ff', 'w': '#d0d0d0'}
all_tiles = AllTile11Tiles(tile_param1=1, tile_param2=1,
              chiralities=chiralities, colors=colors,
              first_tile_angle=2*math.pi*(90/360))
all_tiles.add_all_tiles(input_file_name = 'spectre_config.txt')

all_tiles.footnote = all_tiles.footnote.replace('BASED_ON_TILING',
            'an aperiodic Tile(1,1) tiling')

all_tiles.set_crop_values(
              left_x=all_tiles.get_pt(tile_id='76',
                                      edge=TILE11_EDGE_RENAMER['RD'])[0],
              bottom_y=all_tiles.get_pt(tile_id='127',
                                      edge=TILE11_EDGE_RENAMER['LH'])[1],
              right_x=all_tiles.get_pt(tile_id='229',
                                      edge=TILE11_EDGE_RENAMER['RD'])[0],
              top_y=all_tiles.get_pt(tile_id='167',
                                      edge=TILE11_EDGE_RENAMER['RS'])[1],
                         )

all_tiles.write_points_to_file('tilings/spectre/' +
                               'monochiral_tile_1_1_tiling.txt')
