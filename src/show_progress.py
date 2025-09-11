'''Show progress by changing the color / transparency of tiles on a plane

The purpose is to provide a neat visualization of how much work is remaining
in some task to be done. The program listens for messages on a FIFO, where
the denominator for the percentage is first received, and subsequent messages
indicate the numerator remaining.

As the numerator changes, the proportion of tiles displayed in the 'done'
state is updated, with all tiles starting in the 'start' state and ending in
the 'done' state, when the numerator is 0.

The tile coordinates are read from a text file. Coordinates are multiplied
by the maximum of the height/width shown to make it easier for users to
have tiles displayed in arbitrary window sizes without having to define too
many tiles. The fill and stroke (border) colors for each tile in both the
start and stop states can be specified in the text file. If not provided,
environment variables SHOW_PROGRESS_START_FILL_COLOR, ..._START_STROKE_COLOR,
..._STOP_FILL_COLOR, and ..._STOP_STROKE_COLOR will be used, with other
defaults used if no such variables are specified. Colors should be specified
as rgb or rgba hex strings, e.g. '#ff0000' (solid red), '#00ff0080'
(semi-transparent green). If a column named 'footnote' exists, then the
value from the first row read will be put in a window below the drawing
area.

The denominator can be larger or smaller than the number of tiles.

Tiles that are not visible (i.e., whose edges, transparent or not, are
not contained totally or partially in the display area) are ignored when
calculating the percentage done. This means that resizing the display
window may change the state of visible tiles. However, this redrawing only
occurs after the window becomes inactive after a resize.
'''

from enum import Enum
import csv
import sys
import gi
import os
import random
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
# Do the tiles on the area border first?
BORDER_FIRST = True
# TODO: make command line argument?
TILE_FILE_NAME = 'hat_tiling.txt'

#-----------------------------------------------------------------------------
# Global
#-----------------------------------------------------------------------------
# for testing only
_TEST_WITH_SOLID_COLORS = False
_COLOR = 0

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
# TODO: this fn is also in the program that generates tile coordinates
def hex2(val):
    int_val = int(val)
    if int_val < 0 or int_val > 255:
        raise ValueError(f'Invalid input {val=}')
    ret_val = f'{int_val:02X}'
    return ret_val

def convert_rgba_to_hex(r, g, b, a=None):
    if a is None:
        return f'#{hex2(255*r)}{hex2(255*g)}{hex2(255*b)}'
    else:
        return f'#{hex2(255*r)}{hex2(255*g)}{hex2(255*b)}{hex2(255*a)}'

def get_origin_and_scale(img_width, img_height, w, h):
    #x0 = 0.45*w
    #y0 = 0.45*h
    #print(f'{img_width=}, {img_height=}, {w=}, {h=}')
    #if w/h > img_width/img_height:
    #    scale = w
    #else:
    #    scale = h

    x0, y0 = (0, 0)

    if h == 0:
        return x0, y0, 1

    scale = max(w / img_width, h / img_height)

    return x0, y0, scale

def point_in(pt, w, h):
    '''Boolean wheher pt is in region bounded by (0,0) and (w, h)
    '''
    return 0 <= pt[0] <= w and 0 <= pt[1] <= h

def vint(pt1, pt2, x_val):
    '''Return vertical intercept at given x-val for line.
    '''
    x1, y1 = pt1
    x2, y2 = pt2
    return y1 + (x_val - x1) * (y2 - y1) / (x2 - x1)

def line_crosses(pt1, pt2, w, h):
    '''Check line segment crosses rectangle bounded by (0,0) and (w,h).

    Can assume that both points are outside the rectangle.
    '''
    x1 = pt1[0]
    x2 = pt2[0]
    if x1 < 0 and x2 > 0:
        y_int = vint(pt1, pt2, x_val=0)
        if 0 <= y_int <= h: return True
    elif x2 < 0 and x1 > 0:
        y_int = vint(pt2, pt1, x_val=0)
        if 0 <= y_int <= h: return True
    if x1 < w and x2 > w:
        y_int = vint(pt1, pt2, x_val=w)
        if 0 <= y_int <= h: return True
    elif x2 < w and x1 > w:
        y_int = vint(pt2, pt1, x_val=w)
        if 0 <= y_int <= h: return True
    return False

def convert_hex_to_rgba(hex_str):
    if hex_str[0] != '#' or len(hex_str) not in [7, 9]:
        raise ValueError(f'Invalid color string {hex_str=}')

    hex_str = hex_str[1:]
    if len(hex_str) == 8:
        alpha = int(hex_str[6:], 16) / 255.0
    else:
        alpha = 1.0
    red = int(hex_str[0:2], 16) / 255.0
    blue = int(hex_str[2:4], 16) / 255.0
    green = int(hex_str[4:6], 16) / 255.0
    return (red, blue, green, alpha)

def get_pts_from_reader_row(row):
    pts = []
    ctr = 0
    #print(row)
    while ('px_' + str(ctr) in row and 'py_' + str(ctr) in row):
        pts.append((float(row['px_' + str(ctr)]),
                    float(row['py_' + str(ctr)]))
                  )
        ctr += 1
    if ctr == 0:
        raise ValueError('Variables not found: px_0, py_0, px_1, py_1, ...')
    return pts

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class TileIn(Enum):
    '''Indicator whether tile is inside or outside drawing area.
    '''
    OUT = 0
    IN = 1
    BORDER = 2

class Tile():
    '''Tile to be drawn

    Attributes
    ----------
    user_points : list[(float, float)]
        Vertices of the points on the user surface.
    dw : DrawingArea
        The drawing area holding the list of tiles this tile will
        be stored in.
    device_points : list[(float, float)], optional
        Vertices of the points on the device surface.
    on_border : bool, optional
        Indicates whether tile is on the border of the device surface.
        This is because the `BORDER_FIRST` parameter will toggle the
        appearance of border tiles first.
    tile_in : TileIn, optional
        Indicates whether tile is entirely in the drawing area, outside
        it, or whether it crosses the border. (So there is some redundancy
        here with the `on_border` attribute.)
    change_order : int, optional
        A unique value per tile (from range(len(tiles))) that indicates in
        what order the tile will change from 'start' to 'done' status.
        These values are only reset when the denominator is reset. Higher
        values will be changed first. This is used to set `change_num`, and
        `change_num` is compared to the current numerator to determine
        whether the tile should be drawn in a 'start' or 'stop' state.
    change_num : int, optional
        The numerator value at which a tile should change state from
        'start' to 'stop'. This is updated when the denominator is reset,
        but it can also be updated when the drawing area is resized and the
        `tile_in` or `on_border` attribute changes.
    '''
    def __init__(self, user_points, dw):
        self.user_points = user_points
        # TODO: get rid of the need for this
        self.dw = dw
        self.device_points = None
        self.on_border = None
        self.tile_in = None
        self.change_order = None
        self.change_num = -1
        self.start_fill_color = None
        self.done_fill_color = None

    def draw(self, cr):
        cr.set_line_width(2)
        cr.new_path()
        cr.move_to(self.device_points[0][0], self.device_points[0][1])
        for pt in self.device_points[1:]:
            cr.line_to(pt[0], pt[1])
        cr.close_path()

        if _TEST_WITH_SOLID_COLORS:
            global _COLOR
            if   _COLOR == 0:
                cr.set_source_rgb(1, 0, 0)
            elif _COLOR == 1:
                cr.set_source_rgb(0, 1, 0)
            elif _COLOR == 2:
                cr.set_source_rgb(0, 0, 1)
            if   _COLOR == 3:
                cr.set_source_rgb(1, 1, 0)
            elif _COLOR == 4:
                cr.set_source_rgb(0, 1, 1)
            elif _COLOR == 5:
                cr.set_source_rgb(1, 0, 1)
            elif _COLOR == 6:
                cr.set_source_rgb(0, 0, 0)
            _COLOR = (_COLOR + 1) % 7
            cr.fill_preserve()
            cr.set_source_rgb(0, 0, 0)
        else:
            if self.change_num < self.dw.num:
                cr.set_source_rgba(*self.start_fill_color)
                #pct = self.change_order / len(self.dw.tiles)
                #cr.set_source_rgba(pct, pct, pct, self.start_fill_color[3])
                cr.fill_preserve()
                cr.set_source_rgba(*self.start_stroke_color)
            else:
                cr.set_source_rgba(*self.done_fill_color)
                cr.fill_preserve()
                cr.set_source_rgba(*self.done_stroke_color)

        cr.stroke()

    def set_device_points(self, w, h):
        x0, y0, scale = get_origin_and_scale(self.dw.img_width,
                                             self.dw.img_height, w, h)

        self.device_points = [
            (x0 + scale*val[0], y0 + scale*val[1]) for val in self.user_points]

    def set_tile_in(self, w, h):
        n_pts_in = sum([ point_in(pt, w, h) for pt in self.device_points ])
        if n_pts_in == 0:
            any_crosses = any({
                   line_crosses(self.device_points[i+1],
                                self.device_points[i], w, h)
                   for i in range(len(self.device_points) - 1)
                         })
            if not any_crosses:
                any_crosses= line_crosses(
                               self.device_points[len(self.device_points)-1],
                               self.device_points[0], w, h)
            if any_crosses:
                self.tile_in = TileIn.BORDER
            else:
                self.tile_in = TileIn.OUT
        elif n_pts_in == len(self.device_points):
            self.tile_in = TileIn.IN
        else:
            self.tile_in = TileIn.BORDER

    def set_on_border(self, w, h):
        if self.tile_in == TileIn.BORDER:
            self.on_border = True
        elif self.tile_in == TileIn.OUT:
            self.on_border = False
        else:
            self.on_border = any([ pt[0] in [0, w] or pt[1] in [0, h]
                         for pt in self.device_points])


    def set_color_from_reader_row(self, row, attr):
        if attr in row:
            setattr(self, attr, convert_hex_to_rgba(row[attr]))
        else:
            setattr(self, attr, getattr(self.dw, 'default_' + attr))

class TileDrawingArea(Gtk.DrawingArea):
    '''Drawing area for the tiles

    Attributes
    ----------
    tiles : list[Tile]
        List of the tiles to draw
    full_pad_list : list[int]
        Randomly permuted list [0:denom]. This is reset when the
        denominator is reset. The idea is that we want to reveal
        n(visible_tiles)/denom, every time num decreases by 1. If this
        isn't an integer, then we randomly pick the stages at which an
        additional tile is revealed. The number of additional tiles needed
        may change if the window is resized, but to minimize the change in
        the randomly chosen stages, we sort all the stages randomly and
        pick the number needed from the front of the list.
    denom : int
        Denominator of the percent of work remaining.
    num : int
        Numerator of the percent of work remaining
    pending_dimensions : (int, int), optional
        If the drawing area is resized, this is set to the tuple with the
        new dimensions (w, h). Some expensive or potentially expensive
        tasks are then deferred until the resizing is finished (which is
        very conservatively determined as when the window becomes inactive).
        At this point, the deferred actions are performed and this value
        is reset to None.
    default_start_fill_color : (float, float, float, float)
        Default start fill color in Cairo RGBA format (each value is float
        between 0.0 and 1.0).
    default_start_stroke_color : (float, float, float, float)
        Default start stroke color in Cairo RGBA format.
    default_done_fill_color : (float, float, float, float)
        Default stop fill color in Cairo RGBA format.
    default_done_stroke_color : (float, float, float, float)
        Default stop fill color in Cairo RGBA format.
    '''
    def __init__(self):
        super().__init__()
        self.tiles = []
        self.full_pad_list = []
        self.denom = 1
        self.num = 1
        self.pending_dimensions = None
        self.set_default_tile_colors()

        self.set_size_request(300, 300)
        self.connect('resize', self.on_resize)
        self.set_draw_func(self.on_draw, None)


    def _set_default_color(self, attr, default_value):
        try:
            color_hex_str = os.environ[f'SHOW_PROGRESS_{attr}'.upper()]
        except KeyError:
            color_hex_str = default_value
        setattr(self, 'default_' + attr, convert_hex_to_rgba(color_hex_str))
        #print(getattr(self, 'default_' + attr))

    def set_default_tile_colors(self):
        self._set_default_color('start_fill_color',default_value='#FF0000')
        # TODO: a bit sloppy, as we convert the rgba to a hex str, only to
        # immediately convert it back to rgba
        self._set_default_color('start_stroke_color',
             default_value=convert_rgba_to_hex(*self.default_start_fill_color))
        self._set_default_color('done_fill_color', default_value='#00A933')
        self._set_default_color('done_stroke_color',
              default_value=convert_rgba_to_hex(*self.default_done_fill_color))

    def reset_change_order(self):
        tmp_list = list(range(len(self.tiles)))
        random.shuffle(tmp_list)
        for idx, tile in enumerate(self.tiles):
            tile.change_order = tmp_list[idx]

    # GTK3 had a 'size_allocate' signal, but it was removed in GTK 4.
    # See https://docs.gtk.org/gtk4/migrating-3to4.html#adapt-to-gtkwidgets-size-allocation-changes # pylint: disable=line-too-long
    def on_resize(self, widget, width, height):
        # Called when the drawing area is resized
        self.pending_dimensions = (width, height)
        for tile in self.tiles:
            tile.set_device_points(width, height)
        widget.queue_draw()

    def on_draw(self, area, ctx, w, h, data):  # pylint: disable=unused-argument
        global _COLOR
        _COLOR = 0
        # TODO: could be more efficient
        for tile in self.tiles:
            if tile.change_num >= self.num:
                tile.draw(ctx)

        for tile in self.tiles:
            if tile.change_num < self.num:
                tile.draw(ctx)

    def get_change_num_list(self):
        '''Get a list of all the `change_num` values to use in assignment.

        The returned list has length equal to `len(self.tiles)`. The idea
        is the calling function fill assign each value in the returned
        list to exactly one tile. The list is constructed so approximately
        the same number of visible tiles changes status for each decrement
        of the numerator.

        There is a value of -1 in the list for each tile that is off the
        drawing area (`tile_in = TileIn.OFF`). The rest of the list
        consists of (n(visible tiles) // denom) repetitions of the sequence
        [0:n(visible tiles)]. Random sampling from the same sequence is
        used to complete the required values.

        Suppose there are 100 visible tiles and denominator = 30. Then the
        returned list has a -1 for each off-screen tile and the remainder
        consists of the integers 0, 1, ..., 29 at least 3 times
        (100 // 30 = 3), with 10 of these integers in the list 4 times.
        '''
        n_tiles = len(self.tiles)
        n_visible = sum([tile.tile_in != TileIn.OUT for tile in self.tiles])
        nsamples = n_visible // self.denom
        denom_list = list(range(self.denom))
        final_list = []
        for _ in range(nsamples):
            final_list.extend(denom_list.copy())
        #pad_list = random.sample(denom_list, n_visible - len(final_list))
        pad_list = self.full_pad_list[0:(n_visible - len(final_list))].copy()
        add2_list = [-1]*(n_tiles - n_visible)
        #print(f'{n_visible=}')
        mylist = final_list + pad_list + add2_list
        return mylist

    def set_numerator(self, num):
        '''Set `num` (numerator) and redraw the display area.

        Most of the messages sent by the client will trigger this function.
        '''
        self.num = num
        self.queue_draw()

    def complete_resize(self, w, h):
        '''Complete actions after the drawing area was resized.

        When the drawing area is resized, the window is immediately
        redrawn. However, resizing a window by dragging will send the
        'resize' signal multiple times. There are a few expensive or
        potentially expensive where we just want to wait until the end
        of the resizing. These action include recalculating `tile_in` and
        `on_border` for each tile and resetting `change_num`.

        For now, this function should is called after the dimensions
        change and the window is no longer active.
        '''

        for tile in self.tiles:
            tile.set_device_points(w, h)
            tile.set_tile_in(w, h)
            tile.set_on_border(w, h)
        self.set_change_nums(border_first=BORDER_FIRST)
        self.queue_draw()

    def set_change_nums(self, border_first=False):
        '''Set `tile.change_num` for all tiles in `self.tiles`.

        Parameters
        -----------
        border_first: bool
            Indicates whether tiles with `on_border == True` should be the
            first ones toggled.

        Returns
        -------
        None
        '''
        value_list = self.get_change_num_list()

        if len(value_list) != len(self.tiles):
            raise ValueError(f'should be equal: {len(value_list)=}, '
                             f'{len(self.tiles)=}')

        value_list.sort(reverse=True)

        tile_list = []
        for tile_idx, tile in enumerate(self.tiles):
            if tile.tile_in == TileIn.OUT:
                sort_cat = 2
            elif border_first and tile.on_border:
                sort_cat = 0
            else:
                sort_cat = 1
            tile_list.append((sort_cat, -tile.change_order, tile_idx))
        tile_list.sort()

        for idx, tile_list_item in enumerate(tile_list):
            self.tiles[tile_list_item[2]].change_num = value_list[idx]


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)

        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.box1)

        self.dw = TileDrawingArea()
        self.dw.set_hexpand(True)
        self.dw.set_vexpand(True)
        self.box1.append(self.dw)

        css_provider = Gtk.CssProvider.new()
        css_provider.load_from_data(
            b'.transparent-window { background-color: rgba(0, 0, 0, 0); }')
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self.add_css_class('transparent-window')

        self.load_tiles_from_file(TILE_FILE_NAME)
        self.dw.reset_change_order()
        self.dw.complete_resize(self.get_width(), self.get_height())

    def add_footnote(self, text):
        label = Gtk.Label()
        label.set_markup(text)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_halign(Gtk.Align.FILL)
        label.set_wrap(True)
        label.set_max_width_chars(200)
        self.box1.append(label)
        label.set_name('footnote-label')
        #label.set_hexpand(True)
        #label.set_vexpand(True)

        css_provider = Gtk.CssProvider.new()
        css_provider.load_from_data(
            b'#footnote-label { background-color: white; padding: 5px; }')
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def load_tiles_from_file(self, file_name):
        self.dw.tiles = []
        self.dw.img_width = None
        self.dw.img_height = None
        footnote_text = None
        with open(file_name, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            read_rows = 0
            for row in reader:
                pts = get_pts_from_reader_row(row)
                if read_rows == 0 and 'footnote' in row:
                    footnote_text = row['footnote']
                if read_rows == 0:
                    self.dw.img_height = float(row['img_height'])
                if read_rows == 0:
                    self.dw.img_width = float(row['img_width'])
                new_tile = Tile(user_points=pts, dw=self.dw)
                new_tile.set_color_from_reader_row(row, 'start_fill_color')
                new_tile.set_color_from_reader_row(row, 'done_fill_color')
                new_tile.set_color_from_reader_row(row, 'start_stroke_color')
                new_tile.set_color_from_reader_row(row, 'done_stroke_color')
                self.dw.tiles.append(new_tile)
                read_rows += 1

        if footnote_text:
            self.add_footnote(footnote_text)

class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app_):
        self.win = MainWindow(application=app_)
        self.win.present()
        self.win.connect('notify::is-active', self.on_window_active_changed)
        self.start_fifo_watch()

    def on_window_active_changed(self, widget, pspec): # pylint: disable=unused-argument
        pending_dims = widget.dw.pending_dimensions
        if not widget.props.is_active and pending_dims is not None:
            widget.dw.complete_resize(pending_dims[0], pending_dims[1])
            widget.dw.pending_dimensions = None

    def start_fifo_watch(self):
        try:
            fifo_name = os.environ['SHOW_PROGRESS_FIFO']
        except KeyError:
            print('No `SHOW_PROGRESS_FIFO` environment variable specified. '
                  'Will not listen on FIFO.')
            return False
        # TODO: open in separate thread, as it blocks the main thread
        fifo_channel = GLib.IOChannel.new_file(fifo_name, 'r')
        GLib.io_add_watch(fifo_channel, GLib.IO_IN,
            self.on_fifo_data, priority=GLib.PRIORITY_DEFAULT)
        return True

    def on_fifo_data(self, channel, condition): # pylint: disable=unused-argument
        try:
            # Read a line of data from the FIFO
            _, line, _, _ = channel.read_line()

            if line:
                message = line.strip()
                if message.startswith('R'):
                    # These next two lines are so Anki can send a message
                    # immediately when the Reset Denominator menu item is
                    # clicked. At this point, a card might not even be under
                    # review. The next message will then reset to the correct
                    # denominonator.
                    if message != 'R':
                        self.win.dw.denom = int(message[1:])
                    self.win.dw.reset_change_order()

                    full_pad_list = list(range(self.win.dw.denom))
                    random.shuffle(full_pad_list)
                    self.win.dw.full_pad_list = full_pad_list.copy()
                    self.win.dw.set_change_nums(border_first=BORDER_FIRST)
                    self.win.dw.set_numerator(self.win.dw.denom)
                else:
                    self.win.dw.set_numerator(int(message))

        except GLib.Error as e:
            print(f'Error reading from FIFO: {e}')
            return False

        return True

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

if __name__ == '__main__':
    app = MyApp(application_id='com.github.ghrgriner.penrose')
    app.run(sys.argv)
