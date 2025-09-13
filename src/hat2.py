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

The configuration of the tiles matches that in image 'patch647.png' on the
page https://cs.uwaterloo.ca/~csk/hat/. See LICENSE.txt for complete
attribution details.

The tile generation isn't particularly elegant here. We put the first tile
down and use a configuration file to specify how the other tiles are
placed, by matching an edge of the new tile to an edge on a tile that was
already placed. So extending this program to even larger grids is probably
not advisable.

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
TILE_FILE_NAME = 'hat2_tiling.txt'
INPUT_FILE_NAME = 'hat2_config.txt'
FIRST_TILE_W = 0
FIRST_TILE_H = 0
FIRST_TILE_ANGLE = 0
TILE_PARAM1 = 1
TILE_PARAM2 = math.sqrt(3)
CHIRALITIES = {'r': 'R', 'w': 'R', 'db': 'L', 'g': 'R'}
COLORS = {'r': '#66ccff', 'w': '#ffffff', 'db': '#006699', 'g': '#A0A0A0'}

PointRef = namedtuple('PointRef', ['tile_id', 'edge'])

LEFT_POINT = PointRef(tile_id='254', edge='RT')
BOTTOM_POINT = PointRef(tile_id='128', edge='LN')
RIGHT_POINT = PointRef(tile_id='457', edge='LN')
TOP_POINT = PointRef(tile_id='153', edge='LN')

#-----------------------------------------------------------------------------
# Global
#-----------------------------------------------------------------------------
SCALING = 0.0075
_COLOR = 0
_COLOR_PERIODICITY = 7
TILES = {}

# The hat tiles can be drawn on a hexagonal grid
DISTS = {'FS': SCALING * 2 * TILE_PARAM1, # for hat, full side of hexagon
         'HS': SCALING * TILE_PARAM1,    # for hat, half-side of hexagon
         'HH': SCALING * TILE_PARAM2}  # for hat, half-height of hexagon

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
       tile_id : int
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
       color : str
           The strings are abbreviations for dark blue, light blue, grey,
           and white.
       user_points : list[(float, float)]
           Named tuple storing the coordinates of the dart
    '''
    def __init__(self, tile_id, start_edge, color, match_edge=None,
                 match_id=None, footnote=''):
        self.chirality = CHIRALITIES[color]
        self.tile_id = tile_id
        self.color = color
        self.user_points = None
        self.start_edge = start_edge
        self.match_edge = match_edge
        self.match_id = match_id
        self.footnote = footnote
        self.set_user_points()
        self.set_colors()

    def set_user_points(self):
        if not self.match_edge:
            curr_pt = (FIRST_TILE_W * SCALING, FIRST_TILE_H * SCALING)
            curr_angle = FIRST_TILE_ANGLE
        else:
            match_tile = TILES[self.match_id]
            # the point at `match_pos` is the END of the matching segment
            # when we first drew it, and the previous point in `user_points`
            # is the start.
            match_pos = EDGES[match_tile.chirality].index(self.match_edge)
            match_end = match_tile.user_points[match_pos]
            match_start = match_tile.user_points[(match_pos - 1) % 13]
            if self.chirality == match_tile.chirality:
                # We always need to draw the starting edge in the opposite
                # direction it was first drawn. However, if the chirality
                # of the two tiles differs
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
        if hat.tile_id in TILES:
            raise ValueError(f'id already exists {hat.tile_id=}')
        TILES[hat.tile_id] = hat

    def add_all_tiles(self):
        with open(INPUT_FILE_NAME, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                self.add_hat(Hat(
                    match_id=row['match_id'], match_edge=row['match_edge'],
                    start_edge=row['start_edge'], tile_id=row['tile_id'],
                    color=row['color'], footnote=row['footnote']))

    def get_pt(self, pt_ref):
        '''Get point at the beginning of the edge
        '''
        tile = TILES[pt_ref.tile_id]
        pt_idx = EDGES[tile.chirality].index(pt_ref.edge)
        return tile.user_points[pt_idx]

    def get_boundaries(self):
        left_x = self.get_pt(LEFT_POINT)[0]
        bottom_y = self.get_pt(BOTTOM_POINT)[1]
        right_x = self.get_pt(RIGHT_POINT)[0]
        top_y = self.get_pt(TOP_POINT)[1]
        return left_x, bottom_y, right_x, top_y

    def set_origin(self, left, top):
        for tile in TILES.values():
            new_pts = [
                (pt[0] - left, pt[1] - top)
                for pt in tile.user_points
                      ]
            tile.user_points = new_pts

    def write_points_to_file(self, file_name):
        left, bottom, right, top = self.get_boundaries()
        self.set_origin(left, top)
        img_width = right - left
        img_height = bottom - top
        with open(file_name, 'w', encoding='utf-8') as f:
            max_pts = max([len(tile.user_points) for tile in TILES.values()])
            headers = ('seq_id\tstart_fill_color\tstart_stroke_color\t'
                       'done_fill_color\tdone_stroke_color\tfootnote\t'
                       'img_width\timg_height\t'
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
                f.write(tile.footnote + sep)
                f.write(f'{img_width:.6f}{sep}')
                f.write(f'{img_height:.6f}')
                for pt in tile.user_points:
                    f.write(f'{sep}{pt[0]:.6f}{sep}{pt[1]:.6f}')
                for _ in range(max_pts - len(tile.user_points)):
                    f.write('{sep}{sep}')
                f.write('\n')

# Main Entry Point

all_tiles = AllTiles()
all_tiles.add_all_tiles()
all_tiles.write_points_to_file(TILE_FILE_NAME)

