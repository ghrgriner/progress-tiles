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

The figure can be displayed by putting the (0,0) coordinate at the 45th
percentile of the width and height in a display window and rescaling by the
maximum of the display area height and weight. We chose the scaling factor
to try to display as many tiles as possible without ever having uncovered
portions on any window size. Users who want to see all 223 tiles can make
SCALING smaller, say 0.03.

The program can probably be extended without too much effort to use the
other tiles in the family described by the authors in their paper (i.e.,
the tiles in the continuum from 'chevron' to 'comet').
'''

import math
import csv
from collections import namedtuple

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
TILE_FILE_NAME = 'hat_tiling.txt'
FIRST_TILE_W = -2
FIRST_TILE_H = -2
FIRST_TILE_ANGLE = 2*math.pi*(15/360)

#-----------------------------------------------------------------------------
# Global
#-----------------------------------------------------------------------------
SCALING = 0.041
_COLOR = 0
_COLOR_PERIODICITY = 7
TILES = {}

# The hat tiles can be drawn on a hexagonal grid
DISTS = {'FS': SCALING * 1,      # full side of hexagon
         'HS': SCALING * 0.5,    # half-side of hexagon
         'HH': SCALING * math.sqrt(3)/2}  # half-height of hexagon

# Other direction, i.e., map R to L and vice-versa
OTHER_DIR = {'L': 'R',
             'R': 'L',
             'D': 'D'}

Move = namedtuple('Move', ['turn', 'angle', 'd'])

# start at 'left armpit' of 'left-untucked shirt'
# This is how you draw the hat. First move d, and then turn.
# Note 'left' is from point of view of person wearing the shirt.
LEFT_HAT_MOVES = [
  Move(turn='L', angle=60, d='HS'), # p1
  Move(turn='L', angle=90, d='HS'), # p2
  Move(turn='L', angle=60, d='HH'), # p3
  Move(turn='R', angle=90, d='HH'), # p4
  Move(turn='L', angle=60, d='HS'), # p5
  Move(turn='L', angle=60, d='FS'), # p6
  Move(turn='L', angle=90, d='HS'), # p7
  Move(turn='R', angle=60, d='HH'), # p8
  Move(turn='L', angle=90, d='HH'), # p9
  Move(turn='R', angle=60, d='HS'), # p10
  Move(turn='L', angle=90, d='HS'), # p11
  Move(turn='L', angle=60, d='HH'), # p12
  Move(turn='R', angle=90, d='HH'), # p13
]

# To draw the tile with other chirality, you start at 'right armpit' and
# repeat the same moves, just turning left instead of right and vice-versa.
RIGHT_HAT_MOVES = [ Move(turn=OTHER_DIR[val.turn], angle=val.angle, d=val.d)
                    for val in LEFT_HAT_MOVES ]

# These are some brief abbreviations for the edge names, starting at the
# left pit (see below) and going counter-clockwise around the shirt.
# The nomenclature used is non-standard, but it seems a lot easier if I
# visualize this as an untucked shirt than a hat, the edges are: left
# (arm)pit, left (arm) hole, left shoulder, left neck, right neck, right
# shoulder, right hole, right pit, right torso, right waist, down waist,
# left waist, left torso.
LEFT_EDGES = ['LP','LH','LS','LN','RN','RS',
              'RH','RP','RT','RW','DW','LW','LT']

# If first letter in item is L, make it R and vice-versa, because when
# we draw the tile with the other chirality, we draw it clockwise.
RIGHT_EDGES = [ OTHER_DIR[val[0]] + val[1:] for val in LEFT_EDGES ]

MOVES = {'L' : LEFT_HAT_MOVES, 'R': RIGHT_HAT_MOVES}
EDGES = {'L' : LEFT_EDGES , 'R': RIGHT_EDGES}

COLORS = {'lb': '#66ccff', 'w': '#ffffff', 'db': '#006699', 'g': '#A0A0A0'}
#COLORS = {'lb': '#66ccff', 'w': '#00e000', 'db': '#ff0000', 'g': '#A0A0A0'}

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def convert_rgba_to_hex(r, g, b, a=None):
    if a is None:
        return f'#{r:02X}{g:02X}{b:02X}'
    else:
        return f'#{r:02X}{g:02X}{b:02X}{a:02X}'

def pt_headers(max_pts, sep='\t'):
    ret_list = []
    for i in range(max_pts):
        ret_list.append(f'px_{i}')
        ret_list.append(f'py_{i}')
    return sep.join(ret_list)

def get_angle(start, end):
    y_diff = end[1] - start[1]
    x_diff = end[0] - start[0]
    if abs(x_diff) < .000001:
        if y_diff > 0:
            return math.pi/2
        else:
            return -math.pi/2
    elif x_diff > 0:
        return math.atan(y_diff / x_diff)
    else:
        return math.atan(y_diff / x_diff) + math.pi

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class Hat():
    '''Hat tile

       Attributes
       ----------
       hat_id : int
           Unique integer for each tile
       chirality : str, 'L' or 'R'
           which side of the shirt is 'untucked'
       start_edge : str
           Indicates the edge to start drawing. This should match an edge
           that already exists on another tile so we know what the starting
           position and angle should be. See the items in LEFT_EDGES and
           (equivalently) RIGHT_EDGES for valid values.
       match_edge : str
           When starting to draw a new tile, the edge we start at should
           match the edge of an existing tile so we know the direction and
           angle to start. Of course, for the first tile, this is `None`
           and the starting coordinates and angle are pre-defined.
       match_rev : bool
           We need to know not only the starting edge (from `match_edge`),
           but also which direction on the edge we should go. This can also
           be determined by comparing the chirality of the two tiles. If
           they have the same chirality, then we go in the opposite
           direction.
       color : str, valid values {'db','lb','w','g'}
           The strings are abbreviations for dark blue, light blue, grey,
           and white.
       user_points : list[(float, float)]
           Named tuple storing the coordinates of the dart
    '''
    def __init__(self, hat_id, chirality, start_edge, color, match_edge=None,
                 match_id=None, match_rev='', footnote=''):
        self.chirality = chirality
        self.hat_id = hat_id
        self.color = color
        self.user_points = None
        self.start_edge = start_edge
        self.match_edge = match_edge
        self.match_id = match_id
        self.footnote = footnote
        if match_rev == '':
            self.match_rev = True
        elif match_rev == 'N':
            self.match_rev = False
        else:
            raise ValueError(f'Invalid value {match_rev=}')

        self.set_user_points()
        self.set_colors()

    def set_user_points(self):
        if not self.match_edge:
            curr_pt = (FIRST_TILE_W * SCALING, FIRST_TILE_H * SCALING)
            curr_angle = FIRST_TILE_ANGLE
        else:
            match_tile = TILES[self.match_id]
            # see `Hat` attributes documentation for why this check
            if ((self.chirality != match_tile.chirality and
                self.match_rev) or
               (self.chirality == match_tile.chirality and
                not self.match_rev)):
                raise ValueError('chirality / match_rev mismatch')
            # the point at `match_pos` is the END of the matching segment
            # when we first drew it, and the previous point in `user_points`
            # is the start.
            match_pos = EDGES[match_tile.chirality].index(self.match_edge)
            match_end = match_tile.user_points[match_pos]
            match_start = match_tile.user_points[(match_pos - 1) % 13]
            if self.match_rev:
                # We always need to draw the starting edge in the opposite
                # direction it was first drawn. However, if the chirality
                # of the two tiles differs (equivalently, `match_rev = False`),
                # then we can start at the previous start (since one chirality
                # is drawn counter-clockwise and the other clockwise).
                curr_pt = match_end
                curr_angle = get_angle(start=match_end, end=match_start)
            else:
                curr_pt = match_start
                curr_angle = get_angle(start=match_start, end=match_end)

        pts = []

        start_pos = EDGES[self.chirality].index(self.start_edge)
        move_list = MOVES[self.chirality][start_pos:]
        move_list.extend(MOVES[self.chirality][:start_pos])

        for move in move_list:
            if move.turn == 'L':
                angle_const = -1
            else:
                angle_const = 1
            curr_pt = (
                round(curr_pt[0] + DISTS[move.d] * math.cos(curr_angle),6),
                round(curr_pt[1] + DISTS[move.d] * math.sin(curr_angle),6)
                      )
            # Turn after moving
            curr_angle = curr_angle + angle_const * 2*math.pi * move.angle/360
            pts.append(curr_pt)
        # We might not have started at the appropriate point, so rearrange
        out_list = pts[-start_pos:]
        out_list.extend(pts[:-start_pos])
        #print(out_list)
        self.user_points = out_list

    def set_colors(self):
        global _COLOR
        self.start_fill_color = COLORS[self.color]
        #self.start_fill_color = convert_rgba_to_hex(
        #                              255, 56 + 12*_COLOR, 56 + 12*_COLOR)
        #self.start_stroke_color = convert_rgba_to_hex(255, 56, 56)
        self.start_stroke_color = convert_rgba_to_hex(0, 0, 0)
        #self.done_fill_color = convert_rgba_to_hex(
        #                              56 + 12*_COLOR, 255, 56 + 12*_COLOR)
        #self.done_stroke_color = convert_rgba_to_hex(56, 255, 56)
        self.done_fill_color = convert_rgba_to_hex(0, 0, 0, 0)
        self.done_stroke_color = convert_rgba_to_hex(0, 0, 0, 0)
        _COLOR = (_COLOR + 1) % _COLOR_PERIODICITY

class AllTiles:
    '''Class for holding, loading, and writing to file all the tiles.
    '''
    def __init__(self):
        self.tiles = {}

    def __str__(self):
        return f'tiles={self.tiles}'

    def add_hat(self, hat):
        if hat.hat_id in TILES:
            raise ValueError(f'id already exists {hat.hat_id=}')
        TILES[hat.hat_id] = hat

    def add_all_tiles(self):
        with open('hat_config.txt', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                self.add_hat(Hat(chirality=row['chirality'],
                    match_id=row['match_id'], match_edge=row['match_edge'],
                    start_edge=row['start_edge'], hat_id=row['hat_id'],
                    match_rev=row['match_rev'], color=row['color'],
                    footnote=row['footnote']))

    def write_points_to_file(self, file_name):
        with open(file_name, 'w', encoding='utf-8') as f:
            max_pts = max([len(tile.user_points) for tile in TILES.values()])
            headers = ('seq_id\tstart_fill_color\tstart_stroke_color\t'
                       'done_fill_color\tdone_stroke_color\tfootnote\t'
                       f'{pt_headers(max_pts)}')
            f.write(headers)
            f.write('\n')
            for idx, tile in enumerate(TILES.values()):
                sep = '\t'
                f.write(str(idx) + sep)
                f.write(tile.start_fill_color + sep)
                f.write(tile.start_stroke_color + sep)
                f.write(tile.done_fill_color + sep)
                f.write(tile.done_stroke_color + sep)
                f.write(tile.footnote)
                for pt in tile.user_points:
                    f.write(f'{sep}{pt[0]:.6f}{sep}{pt[1]:.6f}')
                for _ in range(max_pts - len(tile.user_points)):
                    f.write('{sep}{sep}')
                f.write('\n')

# Main Entry Point

all_tiles = AllTiles()
all_tiles.add_all_tiles()
all_tiles.write_points_to_file(TILE_FILE_NAME)

