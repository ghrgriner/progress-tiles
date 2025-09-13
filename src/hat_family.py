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

Defines classes for drawing tiles and collections of tiles in the
Smith-Myers-Kaplan-Goodman-Strauss family. See reference [1] in
../LICENSE.txt for details.

The tile generation isn't particularly elegant here. We put the first tile
down and read a configuration file to specify how the other tiles are
placed, by matching an edge of the new tile to an edge on a tile that was
already placed.
'''

import math
import csv
from collections import namedtuple

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Global
#-----------------------------------------------------------------------------
_FIRST_TILE_W = 0
_FIRST_TILE_H = 0

# The hat tiles can be drawn on a hexagonal grid

# Other direction, i.e., map R to L and vice-versa
OTHER_DIR = {'L': 'R',
             'R': 'L',
             'D': 'D'}

Move = namedtuple('Move', ['turn', 'angle', 'd'])
Segment = namedtuple('Segment', ['start', 'stop'])

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

def dist(pt1, pt2):
    return math.sqrt((pt2[1]-pt1[1])**2 +
                     (pt2[0]-pt1[0])**2)

def pt_headers(max_pts, sep='\t'):
    ret_list = []
    for i in range(max_pts):
        ret_list.append(f'px_{i}')
        ret_list.append(f'py_{i}')
    return sep.join(ret_list)

def get_angle(start, end):
    y_diff = end[1] - start[1]
    x_diff = end[0] - start[0]
    # This will raise an except for now if we try to run on the degenerate
    # tiles ('comet' and 'chevron', since some side lengths are 0, so we can't
    # determine the starting angle from the distance of the two points on the
    # matching edge when the 'edge' is just a point
    if y_diff*y_diff + x_diff*x_diff < .00000001:
        raise ValueError('Cannot get angle since side length 0!')
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
class HatFamilyTile():
    '''Hat-family tile

    Attributes
    ----------
    tile_id : int
        Unique integer for each tile
    chirality : str, 'L' or 'R'
        which side of the shirt is 'untucked' (for hat tiles)
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
    start_fill_color : str
        Fill color for the tile in the 'start' state, as rgb/rgba hex
        string.
    start_stroke_color : str
        Stroke color for the tile in the 'start' state, as rgb/rgba hex
        string.
    done_fill_color : str
        Fill color for the tile in the 'done' state, as rgb/rgba hex
        string.
    done_stroke_color : str
        Stroke color for the tile in the 'done' state, as rgb/rgba hex
        string.
    footnote : str
        Footnote to pass through to the output. However, `show_progress.py`
        will only consider the value on the first non-header row, so this
        doesn't really need to be a tile attribute, but it is for now.
    '''
    def __init__(self, all_tiles, tile_id, start_edge, color, match_edge=None,
                 match_id=None, footnote=''):
        self.chirality = all_tiles.chiralities[color]
        self.tile_id = tile_id
        self.color = color
        self.user_points = None
        self.start_edge = start_edge
        self.match_edge = match_edge
        self.match_id = match_id
        self.footnote = footnote
        self.set_user_points(all_tiles)
        self.set_colors(all_tiles.colors)

    def get_boundary(self, side):
        if side == 'L':
            return min([ pt[0] for pt in self.user_points ])
        elif side == 'R':
            return max([ pt[0] for pt in self.user_points ])
        elif side == 'B':
            return max([ pt[1] for pt in self.user_points ])
        elif side == 'T':
            return min([ pt[1] for pt in self.user_points ])

    def set_user_points(self, all_tiles):
        if not self.match_edge:
            curr_pt = (_FIRST_TILE_W * all_tiles.scaling,
                       _FIRST_TILE_H * all_tiles.scaling)
            curr_angle = all_tiles.first_tile_angle
        else:
            match_tile = all_tiles.tiles[self.match_id]
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
                round(curr_pt[0]
                      + all_tiles.dists[move.d] * math.cos(curr_angle),6),
                round(curr_pt[1]
                      + all_tiles.dists[move.d] * math.sin(curr_angle),6)
                      )
            # Turn after moving
            curr_angle = curr_angle + angle_const * 2*math.pi * move.angle/360
            pts.append(curr_pt)
        # We might not have started at the appropriate point, so rearrange
        out_list = pts[-start_pos:]
        out_list.extend(pts[:-start_pos])
        #print(out_list)
        self.user_points = out_list

    def set_colors(self, colors):
        self.start_fill_color = colors[self.color]
        self.start_stroke_color = convert_rgba_to_hex(0, 0, 0)
        #self.done_fill_color = convert_rgba_to_hex(
        self.done_fill_color = convert_rgba_to_hex(0, 0, 0, 0)
        self.done_stroke_color = convert_rgba_to_hex(0, 0, 0, 0)

class AllTiles:
    '''Class for holding, loading, and writing to file all the tiles.

    Attributes
    ----------
    tile_id : str
        Unique id for each tile
    tile_param1 : float
        One of the side lengths that can be set independently. This is
        the shorter side for the 'hat' tile.
    tile_param2 : float
        The other side length. This is the longer side for the 'hat' tile.
    chiralities : dict[str, Union['L','R']]
        Dictionary that takes the strings representing the color from the
        input file (which is typically a short abbreviation like 'w' for
        'white') and returns the chirality. This is possible since all the
        examples we provide color the opposite chirality with a different
        color.
    colors : dict[str, str]
        Dictionary that takes the strings representing the color from the
        input file (which is typically a short abbreviation like 'w' for
        'white') and returns a rgb or rgba hex string (e.g., '#ff0000').
    first_tile_angle : float, optional (default=0)
        The angle the first edge in the first tile is drawn at.
    scaling : float, optional (default=1)
        Optional scaling. If provided, all distances are multiplied by
        this factor. This is provided for now for backwards compatability.
        It is less important since the window in `show_progress.py` will
        also resize the image.
    left_x : float, optional (default = None)
        Left x-coordinate to use when cropping. If None, then the minimum
        of all x-coordinates of all points is used.
    right_x : float, optional (default = None)
        Right x-coordinate to use when cropping. If None, then the maximum
        of all x-coordinates of all points is used.
    bottom_y : float, optional (default = None)
        Bottom y-coordinate to use when cropping. If None, then the maximum
        of all y-coordinates of all points is used.
    top_y : float, optional (default = None)
        Top y-coordinate to use when cropping. If None, then the minimum
        of all y-coordinates of all points is used.
    '''
    def __init__(self, tile_param1, tile_param2, chiralities, colors,
                 first_tile_angle=0, scaling=1):
        self.tiles = {}
        self.tile_param1 = tile_param1
        self.tile_param2 = tile_param2
        self.chiralities = chiralities
        self.colors = colors
        self.first_tile_angle = first_tile_angle
        self.scaling = scaling
        self.left_x = None
        self.right_x = None
        self.top_y = None
        self.bottom_y = None

        self.dists = {'FS': scaling * 2 * tile_param1,
                 'HS': scaling * tile_param1,
                 'HH': scaling * tile_param2}

    def __str__(self):
        return f'tiles={self.tiles}'

    def set_crop_values(self, left_x=None, bottom_y=None, right_x=None,
                              top_y=None):
        self.left_x = left_x
        self.bottom_y = bottom_y
        self.right_x = right_x
        self.top_y = top_y

    def add_hat(self, hat):
        if hat.tile_id in self.tiles:
            raise ValueError(f'id already exists {hat.tile_id=}')
        self.tiles[hat.tile_id] = hat

    def add_all_tiles(self, input_file_name):
        with open(input_file_name, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                self.add_hat(HatFamilyTile(all_tiles=self,
                    match_id=row['match_id'], match_edge=row['match_edge'],
                    start_edge=row['start_edge'], tile_id=row['tile_id'],
                    color=row['color'], footnote=row['footnote']))

    def get_pt(self, tile_id, edge):
        '''Get point at the end of the edge
        '''
        tile = self.tiles[tile_id]
        pt_idx = EDGES[tile.chirality].index(edge)
        return tile.user_points[pt_idx]

    def get_boundaries(self):
        if self.left_x is None:
            left_x = min(
               [ tile.get_boundary('L') for tile in self.tiles.values() ])
        else:
            left_x = self.left_x

        if self.bottom_y is None:
            bottom_y = max(
               [ tile.get_boundary('B') for tile in self.tiles.values() ])
        else:
            bottom_y = self.bottom_y

        if self.right_x is None:
            right_x = max(
               [ tile.get_boundary('R') for tile in self.tiles.values() ])
        else:
            right_x = self.right_x

        if self.top_y is None:
            top_y = min(
               [ tile.get_boundary('T') for tile in self.tiles.values() ])
        else:
            top_y = self.top_y
        return left_x, bottom_y, right_x, top_y

    def rotate_and_rescale(self, angle, scaling):
        for tile in self.tiles.values():
            new_pts = [
                (scaling*(math.cos(angle)*pt[0] - math.sin(angle)*pt[1]),
                 scaling*(math.sin(angle)*pt[0] + math.cos(angle)*pt[1]))
                for pt in tile.user_points
                      ]
            tile.user_points = new_pts

    def change_coordinates(self,
                           new_segment_coords,
                           old_segment_coords):
        '''Change coordinates based on new/old coordinates for 1 segment.

        This changes the coordinates in `Tile.user_points` for all tiles.
        It doesn't affect the coordinates defined by `self.left_x`,
        `self.right_x`, but this may change in the future.

        The usefulness of the function is as follows. Suppose we have
        a rectangle of 'hat' tiles and want to replace them with other
        tiles in the family (by changing `AllTiles.tile1_param` and
        `AllTiles.tile2_param`), then the approximate rectangle of
        tiles will rotate when the length parameters change. We could
        of course display the rotated graph, but the authors choose an
        animation where the original tiles stay in approximately the
        same location.

        For example, some of the metatiles are surrounded by triskelions
        whose centers form an equilateral triangle. See for example,
        Figure 2.6 in the cited reference. The animation of the authors
        appears to be constructed so that the vertices of at least one of
        these triangles is fixed no matter the length parameter.
        Probably this implies that the vertices of some other such
        triangles are fixed, but it doesn't appear to be true that the
        vertices of all triskelion centers are fixed as the length
        parameter changes. In any case, whether the 'fixing' of the
        vertices of this particular triangle was exact by the authors or
        only a near approximation, treating it as exact closely
        approximate screenshots of the original gif.

        The function parameters are a segment between two of the
        triskelion centers in the reference coordinate system we used to
        draw the 'hat' tiles and a segment between the same points
        represented in the coordinate system we used to draw the other
        tiles.
        '''
        pt1n, pt2n = new_segment_coords.start, new_segment_coords.stop
        pt1o, pt2o = old_segment_coords.start, old_segment_coords.stop
        a1 = get_angle(pt1n, pt2n)
        a2 = get_angle(pt1o, pt2o)
        self.set_origin(pt2o[0], pt2o[1])
        self.rotate_and_rescale(angle=a1-a2,
             scaling=dist(pt1n, pt2n)/dist(pt1o,pt2o))
        self.set_origin(-pt2n[0], -pt2n[1])

    def set_origin(self, left, top):
        for tile in self.tiles.values():
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
            max_pts = max(
                [len(tile.user_points) for tile in self.tiles.values()]
                         )
            headers = ('seq_id\tstart_fill_color\tstart_stroke_color\t'
                       'done_fill_color\tdone_stroke_color\tfootnote\t'
                       'img_width\timg_height\t'
                       f'{pt_headers(max_pts)}')
            f.write(headers)
            f.write('\n')
            for idx, tile in enumerate(self.tiles.values()):
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
