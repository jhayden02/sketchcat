#!/usr/bin/env -S uv run

# sketchcat - A kitty terminal sketchpad kitten.
# Copyright (C) 2025 - Josh Hayden.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from kitty.boss import Boss
from PIL import Image, ImageDraw
from dataclasses import dataclass, field
import sys
import base64
import io
import termios
import tty
import time

class terminal_code:
    query_window_size: str = '\033[14t'
    clear_screen: str = '\033[2J\033[H'
    enable_mouse_modes: str = '\033[?1000h\033[?1003h\033[?1006h\033[?1016h'
    disable_mouse_modes: str = '\033[?1016l\033[?1006l\033[?1003l\033[?1000l'
    kitty_graphics_suffix: str = '\033\\'
    canvas_image_id: int = 1

class config:
    canvas_height: int = 600
    brush_size: int = 5
    brush_color: tuple[int, int, int, int] = (255, 255, 255, 255)
    border_color: tuple[int, int, int, int] = (255, 255, 255, 255)
    max_fps: int = 30

@dataclass
class drawing_state:
    canvas: Image.Image
    drawing_context: ImageDraw.ImageDraw
    canvas_width: int
    is_mouse_down: bool = False
    last_mouse_x: int = -1
    last_mouse_y: int = -1
    needs_redraw: bool = False
    last_render_time: float = field(default_factory=time.time)
    min_frame_time: float = 1.0 / config.max_fps

def get_terminal_width(file_descriptor: int) -> int:
    old_terminal_settings: list = termios.tcgetattr(file_descriptor)

    try:
        tty.setraw(file_descriptor)
        sys.stdout.write(terminal_code.query_window_size)
        sys.stdout.flush()

        terminal_response: str = ''
        while True:
            char: str = sys.stdin.read(1)
            terminal_response += char
            if char == 't':
                break

        response_parts: list[str] = terminal_response.split(';')
        if len(response_parts) >= 3 and response_parts[0] == '\033[4':
            return int(response_parts[2].rstrip('t'))
        return 800
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_terminal_settings)

def init_canvas(width: int, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    canvas: Image.Image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    drawing_context: ImageDraw.ImageDraw = ImageDraw.Draw(canvas)
    drawing_context.rectangle(
        [(0, 0), (width - 1, height - 1)],
        outline=config.border_color,
        width=1
    )
    return canvas, drawing_context

def enable_mouse_tracking() -> None:
    sys.stdout.write(terminal_code.clear_screen)
    sys.stdout.write(terminal_code.enable_mouse_modes)
    sys.stdout.flush()

def disable_mouse_tracking() -> None:
    sys.stdout.write(terminal_code.disable_mouse_modes)
    sys.stdout.flush()

def render_canvas(image: Image.Image) -> None:
    sys.stdout.write(terminal_code.clear_screen)
    buffer: io.BytesIO = io.BytesIO()
    image.save(buffer, format='PNG')
    image_data: bytes = buffer.getvalue()
    encoded_data: str = base64.b64encode(image_data).decode('ascii')

    image_id: int = terminal_code.canvas_image_id

    output: str = (
        f'\033_Gf=100,a=T,t=d,i={image_id};'
        f'{encoded_data}'
        f'{terminal_code.kitty_graphics_suffix}'
    )
    sys.stdout.write(output)
    sys.stdout.flush()

def read_mouse_event() -> tuple[int, int, int, str]:
    mouse_data: str = ''
    while True:
        char: str = sys.stdin.read(1)
        if char in 'mM':
            break
        mouse_data += char

    parts: list[str] = mouse_data.split(';')
    if len(parts) >= 3:
        button: int = int(parts[0])
        x: int = int(parts[1]) - 1
        y: int = int(parts[2]) - 1
        return button, x, y, char
    return -1, -1, -1, ''

def draw_brush(
    drawing_context: ImageDraw.ImageDraw,
    x: int,
    y: int,
    brush_size: int,
    color: tuple[int, int, int, int]
) -> None:
    drawing_context.ellipse(
        [x - brush_size, y - brush_size, x + brush_size, y + brush_size],
        fill=color
    )

def draw_stroke(
    drawing_context: ImageDraw.ImageDraw,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    brush_size: int,
    color: tuple[int, int, int, int]
) -> None:
    drawing_context.line(
        [(x1, y1), (x2, y2)],
        fill=color,
        width=brush_size * 2,
        joint='curve'
    )
    draw_brush(drawing_context, x2, y2, brush_size, color)

def process_drawing(state: drawing_state, x: int, y: int, button: int) -> None:
    is_drawing: bool = state.is_mouse_down and (button == 0 or button == 32)
    if not is_drawing:
        state.last_mouse_x = -1
        state.last_mouse_y = -1
        return

    is_in_bounds: bool = (
        0 <= x < state.canvas_width and 0 <= y < config.canvas_height
    )
    if not is_in_bounds:
        return

    has_moved: bool = state.last_mouse_x != x or state.last_mouse_y != y
    if not has_moved:
        return

    if state.last_mouse_x >= 0 and state.last_mouse_y >= 0:
        draw_stroke(
            state.drawing_context,
            state.last_mouse_x,
            state.last_mouse_y,
            x,
            y,
            config.brush_size,
            config.brush_color
        )
    else:
        draw_brush(
            state.drawing_context, x, y, config.brush_size, config.brush_color
        )

    state.last_mouse_x = x
    state.last_mouse_y = y
    state.needs_redraw = True

def handle_escape_sequence(state: drawing_state) -> bool:
    sequence: str = sys.stdin.read(2)

    if sequence == 'q':
        return True

    if sequence != '[<':
        return False

    button: int
    x: int
    y: int
    event_type: str
    button, x, y, event_type = read_mouse_event()

    if event_type == 'M' and button == 0:
        state.is_mouse_down = True
    elif event_type == 'm' and button == 0:
        state.is_mouse_down = False

    process_drawing(state, x, y, button)
    return False

def reinit_canvas(state: drawing_state) -> None:
    state.canvas, state.drawing_context = init_canvas(
        state.canvas_width, config.canvas_height
    )
    state.needs_redraw = True

def maybe_render(state: drawing_state) -> None:
    current_time: float = time.time()
    if not state.needs_redraw:
        return
    if (current_time - state.last_render_time) < state.min_frame_time:
        return

    render_canvas(state.canvas)
    state.needs_redraw = False
    state.last_render_time = current_time

def run_event_loop(state: drawing_state) -> None:
    while True:
        char: str = sys.stdin.read(1)

        if char == 'q':
            break
        if char == 'c':
            reinit_canvas(state)
        if char == '\033':
            if handle_escape_sequence(state):
                break

        maybe_render(state)

def main(args: list[str]) -> str:
    file_descriptor: int = sys.stdin.fileno()
    canvas_width: int = get_terminal_width(file_descriptor)
    canvas: Image.Image
    ctx: ImageDraw.ImageDraw
    canvas, ctx = init_canvas(canvas_width, config.canvas_height)

    state: drawing_state = drawing_state(
        canvas=canvas,
        drawing_context=ctx,
        canvas_width=canvas_width
    )

    old_terminal_settings: list = termios.tcgetattr(file_descriptor)
    try:
        tty.setraw(file_descriptor)
        enable_mouse_tracking()
        render_canvas(state.canvas)
        run_event_loop(state)
    finally:
        termios.tcsetattr(
            file_descriptor, termios.TCSADRAIN, old_terminal_settings
        )
        disable_mouse_tracking()

    return ''
