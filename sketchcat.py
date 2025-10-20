#!/usr/bin/env python3

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
import sys
import base64
import io
import termios
import tty

class terminal_code:
    query_window_size: str = '\033[14t'
    clear_screen: str = '\033[2J\033[H'
    enable_mouse_modes: str = '\033[?1000h\033[?1003h\033[?1006h\033[?1016h'
    disable_mouse_modes: str = '\033[?1016l\033[?1006l\033[?1003l\033[?1000l'
    kitty_graphics_prefix: str = '\033_Gf=100,a=T,t=d;'
    kitty_graphics_suffix: str = '\033\\'

class config:
    canvas_height: int = 600
    brush_size: int = 5
    brush_color: tuple[int, int, int, int] = (255, 255, 255, 255)
    border_color: tuple[int, int, int, int] = (255, 255, 255, 255)

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
    buffer: io.BytesIO = io.BytesIO()
    image.save(buffer, format='PNG')
    image_data: bytes = buffer.getvalue()
    encoded_data: str = base64.b64encode(image_data).decode('ascii')
    output: str = (
        f'{terminal_code.kitty_graphics_prefix}'
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

def run_event_loop(
    canvas: Image.Image,
    drawing_context: ImageDraw.ImageDraw,
    canvas_width: int,
    file_descriptor: int
) -> None:
    old_terminal_settings: list = termios.tcgetattr(file_descriptor)

    try:
        tty.setraw(file_descriptor)

        is_mouse_down: bool = False
        last_mouse_x: int = -1
        last_mouse_y: int = -1
        needs_redraw: bool = False

        while True:
            char: str = sys.stdin.read(1)

            if char == 'q':
                break

            if char == '\033':
                sequence: str = sys.stdin.read(2)
                if sequence == '[<':
                    button, x, y, event_type = read_mouse_event()

                    if event_type == 'M' and button == 0:
                        is_mouse_down = True
                    elif event_type == 'm' and button == 0:
                        is_mouse_down = False

                    is_drawing: bool = is_mouse_down and (button == 0 or button == 32)
                    is_in_bounds: bool = 0 <= x < canvas_width and 0 <= y < config.canvas_height
                    has_moved: bool = last_mouse_x != x or last_mouse_y != y

                    if is_drawing and is_in_bounds and has_moved:
                        draw_brush(
                            drawing_context,
                            x,
                            y,
                            config.brush_size,
                            config.brush_color
                        )
                        last_mouse_x = x
                        last_mouse_y = y
                        needs_redraw = True
                elif sequence == 'q':
                    break

            if needs_redraw:
                sys.stdout.write(terminal_code.clear_screen)
                render_canvas(canvas)
                needs_redraw = False
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_terminal_settings)
        disable_mouse_tracking()

def main(args: list[str]) -> str:
    file_descriptor: int = sys.stdin.fileno()

    canvas_width: int = get_terminal_width(file_descriptor)
    canvas, drawing_context = init_canvas(canvas_width, config.canvas_height)

    enable_mouse_tracking()
    render_canvas(canvas)

    run_event_loop(canvas, drawing_context, canvas_width, file_descriptor)

    return ''

def handle_result(args: list[str], answer: str, target_window_id: int, boss: Boss) -> None:
    pass
