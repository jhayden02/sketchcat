# sketchcat
A kitty terminal sketchpad kitten.

## Prerequisites

- [Kitty terminal emulator](https://sw.kovidgoyal.net/kitty/)
- Python 3.6 or higher
- Pillow (PIL) library

## Installation

1. Clone the repository:
```bash
git clone https://github.com/BlinkDynamo/sketchcat.git
cd sketchcat
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Symlink the kitten to your kitty config directory:
```bash
ln -s $(pwd -P)/sketchcat.py ~/.config/kitty/sketchcat.py
```

## Usage

If your installation was successful, you may now use
sketchcat in any kitty terminal.
```bash
kitty +kitten sketchcat.py
```

If typing this out everytime feels clunky to you, you
can map a keybind in your `kitty.conf` to launch sketchcat.
```
map ctrl+shift+d kitten sketchcat.py
```

With this added, pressing `Ctrl+Shift+D` in any kitty terminal
will launch sketchcat.

## Controls
Sketchcat is very simple by design. 

- **Left mouse button + drag**: Draw on the canvas
- **q**: Quit and return to terminal

Even after quiting, your drawing will stay in your terminal
until the terminal is cleared.

## Configuration

Edit the `config` class in `sketchcat.py` to customize:

- `canvas_height`: Canvas height in pixels (default: 600)
- `brush_size`: Brush radius in pixels (default: 5)
- `brush_color`: RGBA brush color (default: white)
- `border_color`: RGBA border color (default: white)

Canvas width automatically adjusts to terminal width.

## License

GNU General Public License v3.0
