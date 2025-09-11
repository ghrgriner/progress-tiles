# Create tiling using hexagon tiles.
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

'''Create tiling using hexagon tiles.

The figure can be displayed by putting the (0,0) coordinate at the 45th
percentile of the width and height in a display window and rescaling by the
maximum of the display area height and weight. We chose the scaling factor
to try to display as many tiles as possible without ever having uncovered
portions on any window size.
'''

import math

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
TILE_FILE_NAME = 'honeycomb_tiling.txt'

#-----------------------------------------------------------------------------
# Global
#-----------------------------------------------------------------------------
SCALING = 1  # was 0.08
_COLOR = 0
_COLOR_PERIODICITY = 7

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

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class Hexagon():
    '''Hexagon tile

       Attributes
       ----------
       loc_x : float
           x-coordinate of center of hexagon
       loc_y : float
           y-coordinate of center of hexagon
       user_points : list[(float, float)]
           Named tuple storing the coordinates of the dart
    '''
    def __init__(self, loc_x, loc_y):
        self.loc_x = loc_x
        self.loc_y = loc_y
        self.user_points = None
        self.set_user_points()
        self.set_colors()

    def set_user_points(self):
        p1 = (self.loc_x + SCALING*1, self.loc_y + 0)
        p2 = (self.loc_x + SCALING*0.5, self.loc_y + SCALING*math.sqrt(3)/2)
        p3 = (self.loc_x - SCALING*0.5, self.loc_y + SCALING*math.sqrt(3)/2)
        p4 = (self.loc_x - SCALING*1, self.loc_y)
        p5 = (self.loc_x - SCALING*0.5, self.loc_y - SCALING*math.sqrt(3)/2)
        p6 = (self.loc_x + SCALING*0.5, self.loc_y - SCALING*math.sqrt(3)/2)
        self.user_points = [p1, p2, p3, p4, p5, p6]

    def set_colors(self):
        global _COLOR
        self.start_fill_color = convert_rgba_to_hex(
                                      255, 56 + 12*_COLOR, 56 + 12*_COLOR)
        self.start_stroke_color = convert_rgba_to_hex(255, 56, 56)
        self.done_fill_color = convert_rgba_to_hex(
                                      56 + 12*_COLOR, 255, 56 + 12*_COLOR)
        self.done_stroke_color = convert_rgba_to_hex(56, 255, 56)
        _COLOR = (_COLOR + 1) % _COLOR_PERIODICITY

class AllTiles:
    '''Class for holding, loading, and writing to file all the tiles.
    '''
    def __init__(self):
        self.tiles = []

    def __str__(self):
        return f'tiles={self.tiles}'

    def add_all_tiles(self):
        for y in range(-4, 5):
            for x in range(-6, 9, 3):
                self.tiles.append(Hexagon(loc_x=SCALING*x,
                                          loc_y=SCALING*y*math.sqrt(3)))
                self.tiles.append(Hexagon(loc_x=SCALING*(x + 1.5),
                                       loc_y=SCALING*(y + 0.5)*math.sqrt(3)))

    def set_origin(self, left, top):
        for tile in self.tiles:
            new_pts = [
                (pt[0] - left, pt[1] - top)
                for pt in tile.user_points
                      ]
            tile.user_points = new_pts

    def write_points_to_file(self, file_name):
        #left, bottom, right, top = -6.5, 4, 6.5, -4
        left, bottom, right, top = -6.5, 4.5*math.sqrt(3), 6.5, -4*math.sqrt(3)
        self.set_origin(left, top)
        img_width = right - left
        img_height = bottom - top
        with open(file_name, 'w', encoding='utf-8') as f:
            max_pts = max([len(tile.user_points) for tile in self.tiles])
            headers = ('seq_id\tstart_fill_color\tstart_stroke_color\t'
                       'done_fill_color\tdone_stroke_color\t'
                       'img_width\timg_height\t'
                       f'{pt_headers(max_pts)}')
            f.write(headers)
            f.write('\n')
            for idx, tile in enumerate(self.tiles):
                sep = '\t'
                f.write(str(idx) + sep)
                f.write(tile.start_fill_color + sep)
                f.write(tile.start_stroke_color + sep)
                f.write(tile.done_fill_color + sep)
                f.write(tile.done_stroke_color + sep)
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

#print(all_tiles)
