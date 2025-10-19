from kitty.boss import Boss
from PIL import Image, ImageDraw
import sys
import base64
import io
import termios
import tty

CANVAS_WIDTH: int = 800
CANVAS_HEIGHT: int = 600
BRUSH_SIZE: int = 5
BRUSH_COLOR: tuple[int, int, int] = (0, 0, 255)

def send_image_to_terminal(image: Image.Image) -> None:
    buffer: io.BytesIO = io.BytesIO()
    image.save(buffer, format='PNG')
    image_data: bytes = buffer.getvalue()
    encoded_data: str = base64.b64encode(image_data).decode('ascii')

    sys.stdout.write(f'\033_Gf=100,a=T,t=d;{encoded_data}\033\\')
    sys.stdout.flush()

def main(args: list[str]) -> str:
    canvas: Image.Image = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), 'white')
    draw: ImageDraw.ImageDraw = ImageDraw.Draw(canvas)

    sys.stdout.write('\033[2J\033[H')
    sys.stdout.write('\033[?1000h\033[?1003h\033[?1006h\033[?1016h')
    sys.stdout.flush()

    send_image_to_terminal(canvas)

    fd: int = sys.stdin.fileno()
    old_settings: list = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        mouse_down: bool = False
        last_x: int = -1
        last_y: int = -1

        while True:
            char: str = sys.stdin.read(1)

            if char == '\033':
                next_char: str = sys.stdin.read(1)
                if next_char == '[':
                    seq: str = sys.stdin.read(1)
                    if seq == '<':
                        mouse_data: str = ''
                        while True:
                            c: str = sys.stdin.read(1)
                            if c in 'mM':
                                break
                            mouse_data += c

                        parts: list[str] = mouse_data.split(';')
                        if len(parts) >= 3:
                            button: int = int(parts[0])
                            x: int = int(parts[1]) - 1
                            y: int = int(parts[2]) - 1

                            if c == 'M' and button == 0:
                                mouse_down = True
                            elif c == 'm' and button == 0:
                                mouse_down = False

                            if mouse_down and (button == 0 or button == 32):
                                if 0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT:
                                    draw.ellipse(
                                        [
                                            x - BRUSH_SIZE,
                                            y - BRUSH_SIZE,
                                            x + BRUSH_SIZE,
                                            y + BRUSH_SIZE
                                        ],
                                        fill=BRUSH_COLOR
                                    )

                                    sys.stdout.write('\033[2J\033[H')
                                    send_image_to_terminal(canvas)
                elif next_char == 'q':
                    break
            elif char == 'q':
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write('\033[?1016l\033[?1006l\033[?1003l\033[?1000l')
        sys.stdout.flush()

    return ''

def handle_result(args: list[str], answer: str, target_window_id: int, boss: Boss) -> None:
    pass
